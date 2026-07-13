from pathlib import Path
from urllib.parse import quote

import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import AttachmentNotFound, IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueAttachment

_DOWNLOAD_URL = (
    "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/7698/image.png"
)


class TestIssueGetAttachments:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        attachment_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/1",
            "id": "attachment-123",
            "name": "test_file.txt",
            "content": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/1/content",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
            "mimetype": "text/plain",
            "size": 1024,
        }
        attachments_response = [attachment_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments",
                payload=attachments_response,
            )

            result = await tracker_client.issue_get_attachments("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueAttachment)
            assert result[0].name == "test_file.txt"

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/attachments",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_attachments("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueDownloadAttachment:
    async def test_success_streams_chunks(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        # Body larger than default chunk size so iter_chunked actually loops.
        file_content = b"x" * 5000
        destination = tmp_path / "TEST-123-7698.png"

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, body=file_content)

            size = await tracker_client.issue_download_attachment(
                "TEST-123",
                "7698",
                "image.png",
                destination,
                max_bytes=10_000,
            )

            assert size == len(file_content)
            assert destination.read_bytes() == file_content

    async def test_not_found(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "NOTFOUND-123-1.txt"

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/attachments/1/file.txt",
                status=404,
            )

            with pytest.raises(AttachmentNotFound) as exc_info:
                await tracker_client.issue_download_attachment(
                    "NOTFOUND-123",
                    "1",
                    "file.txt",
                    destination,
                    max_bytes=1024,
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"
            assert exc_info.value.attachment_id == "1"
            assert exc_info.value.file_name == "file.txt"
            assert not destination.exists()

    async def test_rejects_by_content_length(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"
        max_bytes = 100

        with aioresponses() as m:
            m.get(
                _DOWNLOAD_URL,
                body=b"never read",
                headers={"Content-Length": str(max_bytes + 1)},
            )

            with pytest.raises(ValueError, match="exceeds limit"):
                await tracker_client.issue_download_attachment(
                    "TEST-123",
                    "7698",
                    "image.png",
                    destination,
                    max_bytes=max_bytes,
                )

            assert not destination.exists()

    async def test_rejects_mid_stream_without_content_length(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"
        max_bytes = 100
        body = b"y" * (max_bytes + 1)

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, body=body)

            with pytest.raises(ValueError, match="exceeds limit"):
                await tracker_client.issue_download_attachment(
                    "TEST-123",
                    "7698",
                    "image.png",
                    destination,
                    max_bytes=max_bytes,
                )

            assert not destination.exists()

    async def test_cleans_up_partial_file_on_mid_stream_reject(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"
        max_bytes = 64
        # Larger than one 64 KiB chunk? No — use small max so first chunks exceed.
        body = b"z" * 200

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, body=body)

            with pytest.raises(ValueError, match="exceeds limit"):
                await tracker_client.issue_download_attachment(
                    "TEST-123",
                    "7698",
                    "image.png",
                    destination,
                    max_bytes=max_bytes,
                )

            assert not destination.exists()

    async def test_does_not_overwrite_existing_destination(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"
        destination.write_bytes(b"existing")

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, body=b"new content")

            with pytest.raises(ValueError, match="Attachment file already exists"):
                await tracker_client.issue_download_attachment(
                    "TEST-123",
                    "7698",
                    "image.png",
                    destination,
                    max_bytes=10_000,
                )

            assert destination.read_bytes() == b"existing"

    @pytest.mark.parametrize(
        ("file_name", "expected_segment"),
        [
            ("a/b.png", "b.png"),
            ("../../v3/issues/X", "X"),
            ("файл.png", quote("файл.png", safe="")),
            ("my file.png", quote("my file.png", safe="")),
        ],
    )
    async def test_file_name_path_is_sanitized(
        self,
        tracker_client: TrackerClient,
        tmp_path: Path,
        file_name: str,
        expected_segment: str,
    ) -> None:
        file_content = b"payload"
        destination = tmp_path / "out.bin"

        with aioresponses() as m:
            m.get(
                (
                    "https://api.tracker.yandex.net/v3/issues/TEST-123/"
                    f"attachments/7698/{expected_segment}"
                ),
                body=file_content,
            )

            size = await tracker_client.issue_download_attachment(
                "TEST-123",
                "7698",
                file_name,
                destination,
                max_bytes=1024,
            )

            assert size == len(file_content)
            assert destination.read_bytes() == file_content

    @pytest.mark.parametrize(
        ("issue_id", "attachment_id"),
        [
            ("../../evil", "1"),
            ("TEST-123", "../attachments/1"),
            ("TEST/123", "1"),
        ],
    )
    async def test_invalid_identifiers_raise_before_http(
        self,
        tracker_client: TrackerClient,
        tmp_path: Path,
        issue_id: str,
        attachment_id: str,
    ) -> None:
        destination = tmp_path / "out.bin"

        with aioresponses() as m:
            with pytest.raises(ValueError, match="contains unsafe characters"):
                await tracker_client.issue_download_attachment(
                    issue_id,
                    attachment_id,
                    "file.txt",
                    destination,
                    max_bytes=1024,
                )

            assert not (m.requests or {})
            assert not destination.exists()

    async def test_forbidden_raises(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, status=403)

            with pytest.raises(ClientResponseError):
                await tracker_client.issue_download_attachment(
                    "TEST-123",
                    "7698",
                    "image.png",
                    destination,
                    max_bytes=1024,
                )

            assert not destination.exists()

    async def test_server_error_raises(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, status=500)

            with pytest.raises(ClientResponseError):
                await tracker_client.issue_download_attachment(
                    "TEST-123",
                    "7698",
                    "image.png",
                    destination,
                    max_bytes=1024,
                )

            assert not destination.exists()

    async def test_empty_body_succeeds(
        self, tracker_client: TrackerClient, tmp_path: Path
    ) -> None:
        destination = tmp_path / "TEST-123-7698.png"

        with aioresponses() as m:
            m.get(_DOWNLOAD_URL, body=b"")

            size = await tracker_client.issue_download_attachment(
                "TEST-123",
                "7698",
                "image.png",
                destination,
                max_bytes=1024,
            )

            assert size == 0
            assert destination.exists()
            assert destination.read_bytes() == b""
