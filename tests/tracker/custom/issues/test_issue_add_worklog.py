import datetime

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import Worklog
from tests.aioresponses_utils import RequestCapture


class TestIssueAddWorklog:
    async def test_success_minimal(self, tracker_client: TrackerClient) -> None:
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

        capture = RequestCapture(payload=worklog_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog",
                callback=capture.callback,
            )

            result = await tracker_client.issue_add_worklog("TEST-123", duration="PT4H")

            assert isinstance(result, Worklog)
            assert result.id == 123
            assert result.comment == "Work done on the issue"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"duration": "PT4H"})

    async def test_success_with_comment_and_start(
        self, tracker_client: TrackerClient
    ) -> None:
        worklog_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog/2",
            "id": 124,
            "version": 1,
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
                "id": "issue-123",
                "key": "TEST-123",
                "display": "Test issue",
            },
            "comment": "Investigated root cause",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
            "duration": "PT30M",
            "start": "2023-01-01T12:00:00.000+0000",
        }

        capture = RequestCapture(payload=worklog_data)
        start = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog",
                callback=capture.callback,
            )

            result = await tracker_client.issue_add_worklog(
                "TEST-123",
                duration="PT30M",
                comment="Investigated root cause",
                start=start,
            )

            assert isinstance(result, Worklog)
            assert result.id == 124

        capture.assert_called_once()
        capture.last_request.assert_json_field("duration", "PT30M")
        capture.last_request.assert_json_field("comment", "Investigated root cause")
        # В запросе используем формат без двоеточия в смещении (+0000)
        capture.last_request.assert_json_field("start", "2023-01-01T12:00:00.000000+0000")

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/worklog",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_add_worklog("NOTFOUND-123", duration="PT1H")

            assert exc_info.value.issue_id == "NOTFOUND-123"


