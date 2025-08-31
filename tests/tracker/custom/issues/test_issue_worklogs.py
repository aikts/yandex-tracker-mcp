import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import Worklog


class TestIssueGetWorklogs:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        worklog_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog/1",
            "id": 123,
            "version": 1,
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
                "id": "issue-123",
                "key": "TEST-123",
                "display": "Test issue",
            },
            "comment": "Work done on the issue",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
            "duration": "PT4H",
        }
        worklogs_response = [worklog_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog",
                payload=worklogs_response,
            )

            result = await tracker_client.issue_get_worklogs("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Worklog)
            assert result[0].comment == "Work done on the issue"

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/worklog",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_worklogs("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"
