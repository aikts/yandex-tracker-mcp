from typing import Any

import pytest
from aiohttp import ClientTimeout
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound, TrackerAPITimeout
from mcp_tracker.tracker.proto.types.issues import IssueAttachment
from tests.aioresponses_utils import RequestCapture

UPLOAD_URL = "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/"

# Not valid UTF-8, with the bytes a text-mode round trip would mangle.
FILE_CONTENT = b"\x89PNG\r\n\x1a\n\x00\xff binary\nbody"


@pytest.fixture
def uploaded_attachment_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/4159",
        "id": "4159",
        "name": "скриншот.png",
        "content": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/4159/скриншот.png",
        "thumbnail": "https://api.tracker.yandex.net/v3/issues/TEST-123/thumbnails/4159",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "createdAt": "2026-09-25T12:00:00.000+0000",
        "mimetype": "image/png",
        "size": len(FILE_CONTENT),
    }


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


class TestIssueAddAttachment:
    async def test_sends_the_file_as_multipart_with_the_filename(
        self,
        tracker_client: TrackerClient,
        uploaded_attachment_data: dict[str, Any],
    ) -> None:
        capture = RequestCapture(status=201, payload=uploaded_attachment_data)

        with aioresponses() as m:
            m.post(f"{UPLOAD_URL}?filename=скриншот.png", callback=capture.callback)

            result = await tracker_client.issue_add_attachment(
                "TEST-123", content=FILE_CONTENT, filename="скриншот.png"
            )

        capture.assert_called_once()
        request = capture.last_request
        assert request.url.path == "/v3/issues/TEST-123/attachments/"
        request.assert_param("filename", "скриншот.png")
        request.assert_headers(
            {"Authorization": "OAuth test-token", "X-Org-ID": "test-org"}
        )

        parts = await request.get_multipart_parts()
        assert len(parts) == 1
        assert parts[0].name == "file"
        assert parts[0].filename == "скриншот.png"
        assert parts[0].content_type == "image/png"
        assert parts[0].content == FILE_CONTENT

        assert isinstance(result, IssueAttachment)
        assert result.id == "4159"
        assert result.name == "скриншот.png"

    async def test_unknown_extension_is_sent_as_octet_stream(
        self,
        tracker_client: TrackerClient,
        uploaded_attachment_data: dict[str, Any],
    ) -> None:
        capture = RequestCapture(status=201, payload=uploaded_attachment_data)

        with aioresponses() as m:
            m.post(f"{UPLOAD_URL}?filename=dump.qwx", callback=capture.callback)

            await tracker_client.issue_add_attachment(
                "TEST-123", content=FILE_CONTENT, filename="dump.qwx"
            )

        parts = await capture.last_request.get_multipart_parts()
        assert parts[0].content_type == "application/octet-stream"

    async def test_uses_the_upload_timeout_not_the_api_one(
        self, uploaded_attachment_data: dict[str, Any]
    ) -> None:
        client = TrackerClient(
            token="test-token", org_id="test-org", timeout=10, upload_timeout=600
        )
        capture = RequestCapture(status=201, payload=uploaded_attachment_data)

        try:
            with aioresponses() as m:
                m.post(f"{UPLOAD_URL}?filename=a.png", callback=capture.callback)

                await client.issue_add_attachment(
                    "TEST-123", content=FILE_CONTENT, filename="a.png"
                )
        finally:
            await client.close()

        assert capture.last_request.timeout == ClientTimeout(total=600)

    async def test_a_timeout_points_at_the_upload_setting(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.post(f"{UPLOAD_URL}?filename=a.png", exception=TimeoutError())

            with pytest.raises(TrackerAPITimeout) as exc_info:
                await tracker_client.issue_add_attachment(
                    "TEST-123", content=FILE_CONTENT, filename="a.png"
                )

        assert exc_info.value.timeout == tracker_client._upload_timeout
        assert exc_info.value.setting == "TRACKER_UPLOAD_TIMEOUT"
        assert "TRACKER_UPLOAD_TIMEOUT" in str(exc_info.value)

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/attachments/?filename=a.png",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_add_attachment(
                    "NOTFOUND-123", content=FILE_CONTENT, filename="a.png"
                )

        assert exc_info.value.issue_id == "NOTFOUND-123"
