import datetime

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import Worklog
from tests.aioresponses_utils import RequestCapture


class TestIssueUpdateWorklog:
    async def test_success_updates_fields(self, tracker_client: TrackerClient) -> None:
        worklog_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog/10",
            "id": 10,
            "version": 2,
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
                "id": "issue-123",
                "key": "TEST-123",
                "display": "Test issue",
            },
            "comment": "Updated comment",
            "createdAt": "2023-01-01T12:00:00.000+0000",
            "duration": "PT2H",
            "start": "2023-01-01T09:00:00.000+0000",
        }

        capture = RequestCapture(payload=worklog_data)
        start = datetime.datetime(2023, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog/10",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update_worklog(
                "TEST-123",
                10,
                duration="PT2H",
                comment="Updated comment",
                start=start,
            )

            assert isinstance(result, Worklog)
            assert result.id == 10

        capture.assert_called_once()
        capture.last_request.assert_json_field("duration", "PT2H")
        capture.last_request.assert_json_field("comment", "Updated comment")
        capture.last_request.assert_json_field(
            "start", "2023-01-01T09:00:00.000000+0000"
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/worklog/10",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_update_worklog(
                    "NOTFOUND-123",
                    10,
                    comment="x",
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueDeleteWorklog:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog/10",
                callback=capture.callback,
            )

            await tracker_client.issue_delete_worklog("TEST-123", 10)

        capture.assert_called_once()

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/worklog/10",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_delete_worklog("NOTFOUND-123", 10)

            assert exc_info.value.issue_id == "NOTFOUND-123"
