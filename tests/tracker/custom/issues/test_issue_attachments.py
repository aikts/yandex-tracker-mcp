from urllib.parse import quote

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueAttachment


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
    async def test_success(self, tracker_client: TrackerClient) -> None:
        file_content = b"hello attachment"

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/7698/image.png",
                body=file_content,
            )

            result = await tracker_client.issue_download_attachment(
                "TEST-123",
                "7698",
                "image.png",
            )

            assert result == file_content

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/attachments/1/file.txt",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_download_attachment(
                    "NOTFOUND-123",
                    "1",
                    "file.txt",
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"

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
        file_name: str,
        expected_segment: str,
    ) -> None:
        file_content = b"payload"

        with aioresponses() as m:
            m.get(
                (
                    "https://api.tracker.yandex.net/v3/issues/TEST-123/"
                    f"attachments/7698/{expected_segment}"
                ),
                body=file_content,
            )

            result = await tracker_client.issue_download_attachment(
                "TEST-123",
                "7698",
                file_name,
            )

            assert result == file_content

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
        issue_id: str,
        attachment_id: str,
    ) -> None:
        with aioresponses() as m:
            with pytest.raises(ValueError, match="contains unsafe characters"):
                await tracker_client.issue_download_attachment(
                    issue_id,
                    attachment_id,
                    "file.txt",
                )

            assert len(m.requests) == 0
