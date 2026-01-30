import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueComment
from tests.aioresponses_utils import RequestCapture


class TestIssueAddComment:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        comment_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/1",
            "id": 1,
            "text": "Hello from test",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
        }

        capture = RequestCapture(payload=comment_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments",
                callback=capture.callback,
            )

            result = await tracker_client.issue_add_comment(
                "TEST-123", text="Hello from test"
            )

            assert isinstance(result, IssueComment)
            assert result.id == 1
            assert result.text == "Hello from test"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"text": "Hello from test"})

    async def test_success_with_summonees(self, tracker_client: TrackerClient) -> None:
        comment_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/2",
            "id": 2,
            "text": "Ping",
            "summonees": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                    "id": "user123",
                    "display": "Test User",
                }
            ],
            "createdAt": "2023-01-01T12:00:00.000+0000",
        }

        capture = RequestCapture(payload=comment_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments",
                callback=capture.callback,
            )

            result = await tracker_client.issue_add_comment(
                "TEST-123", text="Ping", summonees=["user123"]
            )

            assert isinstance(result, IssueComment)
            assert result.id == 2
            assert result.summonees is not None

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"text": "Ping", "summonees": ["user123"]}
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/comments",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_add_comment("NOTFOUND-123", text="x")

            assert exc_info.value.issue_id == "NOTFOUND-123"
