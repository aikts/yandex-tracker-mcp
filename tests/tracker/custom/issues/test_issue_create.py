from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


@pytest.fixture
def created_issue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-456",
        "id": "593cd211ef7e8a33********",
        "key": "TEST-456",
        "version": 1,
        "summary": "New issue summary",
        "description": "New issue description",
        "status": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Open",
        },
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "type": {
            "self": "https://api.tracker.yandex.net/v3/issuetypes/2",
            "id": "2",
            "key": "task",
            "display": "Task",
        },
        "priority": {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "key": "normal",
            "display": "Normal",
        },
    }


class TestIssueCreate:
    async def test_success_minimal(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"
            assert result.summary == "New issue summary"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
            }
        )

    async def test_success_with_description(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                description="New issue description",
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
                "description": "New issue description",
            }
        )

    async def test_success_with_all_params(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                description="New issue description",
                type=2,
                assignee="user123",
                priority="normal",
                parent="TEST-100",
                sprint=["sprint1", "sprint2"],
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
                "description": "New issue description",
                "type": 2,
                "assignee": "user123",
                "priority": "normal",
                "parent": "TEST-100",
                "sprint": ["sprint1", "sprint2"],
            }
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        created_issue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issue_create(
                queue="TEST",
                summary="New issue summary",
                auth=yandex_auth_cloud,
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_with_assignee_as_int(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                assignee=1234567890,
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["assignee"] == 1234567890

    async def test_with_priority_as_int(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                priority=2,
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["priority"] == 2
