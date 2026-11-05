from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    AttachmentNotFound,
    AttachmentTooLarge,
    IssueNotFound,
)
from mcp_tracker.tracker.proto.types.issues import AttachmentContent

LIST_URL = "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments"
DOWNLOAD_URL = "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/42/{name}"


def attachment_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/42",
        "id": "42",
        "name": "notes.txt",
        "content": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/42/notes.txt",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "createdAt": "2023-01-01T12:00:00.000+0000",
        "mimetype": "text/plain",
        "size": 5,
    }
    payload.update(overrides)
    return payload


class TestIssueGetAttachmentContent:
    async def test_downloads_the_file(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload()])
            m.get(DOWNLOAD_URL.format(name="notes.txt"), body=b"hello")

            result = await tracker_client.issue_get_attachment_content(
                "TEST-123", "42", max_bytes=1024
            )

        assert result == AttachmentContent(
            name="notes.txt", mimetype="text/plain", data=b"hello"
        )

    @pytest.mark.parametrize(
        ("name", "encoded"),
        [
            ("report 2026.pdf", "report%202026.pdf"),
            ("a/b.txt", "a%2Fb.txt"),
            ("отчёт.txt", "%D0%BE%D1%82%D1%87%D1%91%D1%82.txt"),
        ],
    )
    async def test_file_name_is_percent_encoded_in_the_url(
        self, tracker_client: TrackerClient, name: str, encoded: str
    ) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload(name=name)])
            m.get(DOWNLOAD_URL.format(name=encoded), body=b"hello")

            result = await tracker_client.issue_get_attachment_content(
                "TEST-123", "42", max_bytes=1024
            )

        assert result.name == name
        assert result.data == b"hello"

    async def test_mimetype_falls_back_to_the_response_content_type(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload(mimetype=None)])
            m.get(
                DOWNLOAD_URL.format(name="notes.txt"),
                body=b"hello",
                content_type="text/csv",
            )

            result = await tracker_client.issue_get_attachment_content(
                "TEST-123", "42", max_bytes=1024
            )

        assert result.mimetype == "text/csv"

    async def test_unknown_attachment_id(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload()])

            with pytest.raises(AttachmentNotFound) as exc_info:
                await tracker_client.issue_get_attachment_content(
                    "TEST-123", "999", max_bytes=1024
                )

        assert exc_info.value.issue_id == "TEST-123"
        assert exc_info.value.attachment_id == "999"

    async def test_download_answering_404(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload()])
            m.get(DOWNLOAD_URL.format(name="notes.txt"), status=404)

            with pytest.raises(AttachmentNotFound):
                await tracker_client.issue_get_attachment_content(
                    "TEST-123", "42", max_bytes=1024
                )

    @pytest.mark.parametrize(
        "issue_id",
        [
            "",
            "TEST",
            "TEST-",
            "TEST-abc",
            "../TEST-123",
            "TEST-123/../../v3/myself",
            "TEST-123/attachments",
            "TEST-123?expand=x",
            "TEST-123#x",
            "TEST-123 ",
            "TEST-12" + chr(10) + "3",
            "ТЕСТ-123",
        ],
    )
    async def test_malformed_issue_key_is_refused_without_a_request(
        self, tracker_client: TrackerClient, issue_id: str
    ) -> None:
        with aioresponses() as m:
            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_attachment_content(
                    issue_id, "42", max_bytes=1024
                )

        assert exc_info.value.issue_id == issue_id
        assert not m.requests

    @pytest.mark.parametrize("issue_id", ["TEST-123", "my_queue2-7"])
    async def test_ordinary_issue_keys_are_accepted(
        self, tracker_client: TrackerClient, issue_id: str
    ) -> None:
        base = f"https://api.tracker.yandex.net/v3/issues/{issue_id}/attachments"
        with aioresponses() as m:
            m.get(base, payload=[attachment_payload()])
            m.get(f"{base}/42/notes.txt", body=b"hello")

            result = await tracker_client.issue_get_attachment_content(
                issue_id, "42", max_bytes=1024
            )

        assert result.data == b"hello"

    async def test_unknown_issue(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, status=404)

            with pytest.raises(IssueNotFound):
                await tracker_client.issue_get_attachment_content(
                    "TEST-123", "42", max_bytes=1024
                )

    async def test_size_over_the_limit_is_refused_before_downloading(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload(size=2048)])

            with pytest.raises(AttachmentTooLarge) as exc_info:
                await tracker_client.issue_get_attachment_content(
                    "TEST-123", "42", max_bytes=1024
                )

        assert exc_info.value.size == 2048
        assert exc_info.value.limit == 1024
        assert len(m.requests) == 1

    async def test_body_over_the_limit_is_refused_when_size_is_unknown(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload(size=None)])
            m.get(DOWNLOAD_URL.format(name="notes.txt"), body=b"123456")

            with pytest.raises(AttachmentTooLarge) as exc_info:
                await tracker_client.issue_get_attachment_content(
                    "TEST-123", "42", max_bytes=5
                )

        assert exc_info.value.size is None
        assert "TRACKER_ATTACHMENT_MAX_BYTES" in str(exc_info.value)

    async def test_file_exactly_at_the_limit_is_returned(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(LIST_URL, payload=[attachment_payload(size=5)])
            m.get(DOWNLOAD_URL.format(name="notes.txt"), body=b"12345")

            result = await tracker_client.issue_get_attachment_content(
                "TEST-123", "42", max_bytes=5
            )

        assert result.data == b"12345"
