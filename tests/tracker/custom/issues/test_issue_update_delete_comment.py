import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueComment
from tests.aioresponses_utils import RequestCapture


class TestIssueUpdateComment:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        comment_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/10",
            "id": 10,
            "text": "Updated text",
            "updatedAt": "2023-01-01T12:00:00.000+0000",
        }

        capture = RequestCapture(payload=comment_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/10",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update_comment(
                "TEST-123", 10, text="Updated text"
            )

            assert isinstance(result, IssueComment)
            assert result.id == 10
            assert result.text == "Updated text"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"text": "Updated text"})

    async def test_success_with_summonees(self, tracker_client: TrackerClient) -> None:
        comment_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/11",
            "id": 11,
            "text": "Updated with summon",
            "summonees": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                    "id": "user123",
                    "display": "Test User",
                }
            ],
            "updatedAt": "2023-01-01T12:00:00.000+0000",
        }

        capture = RequestCapture(payload=comment_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/11",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update_comment(
                "TEST-123", 11, text="Updated with summon", summonees=["user123"]
            )

            assert isinstance(result, IssueComment)
            assert result.id == 11
            assert result.summonees is not None

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"text": "Updated with summon", "summonees": ["user123"]}
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/comments/10",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_update_comment("NOTFOUND-123", 10, text="x")

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueDeleteComment:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/10",
                callback=capture.callback,
            )

            await tracker_client.issue_delete_comment("TEST-123", 10)

        capture.assert_called_once()

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/comments/10",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_delete_comment("NOTFOUND-123", 10)

            assert exc_info.value.issue_id == "NOTFOUND-123"
