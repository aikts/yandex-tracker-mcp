from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


@pytest.fixture
def moved_issue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/NEWQUEUE-42",
        "id": "593cd211ef7e8a33********",
        "key": "NEWQUEUE-42",
        "version": 2,
        "summary": "Test issue",
        "status": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Open",
        },
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/NEWQUEUE",
            "id": "10",
            "key": "NEWQUEUE",
            "display": "New Queue",
        },
    }


class TestIssueMove:
    async def test_success(
        self, tracker_client: TrackerClient, moved_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/_move?queue=NEWQUEUE",
                callback=capture.callback,
            )

            result = await tracker_client.issue_move("TEST-123", "NEWQUEUE")

            assert isinstance(result, Issue)
            assert result.key == "NEWQUEUE-42"

        capture.assert_called_once()

    async def test_sends_queue_as_query_param(
        self, tracker_client: TrackerClient, moved_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/_move?queue=TARGET",
                callback=capture.callback,
            )

            await tracker_client.issue_move("TEST-123", "TARGET")

        capture.assert_called_once()
        assert capture.last_request.url.query_string == "queue=TARGET"

    async def test_not_found_raises_issue_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        from mcp_tracker.tracker.custom.errors import IssueNotFound

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/MISSING-1/_move?queue=NEWQUEUE",
                status=404,
            )

            with pytest.raises(IssueNotFound):
                await tracker_client.issue_move("MISSING-1", "NEWQUEUE")

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        moved_issue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/_move?queue=NEWQUEUE",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issue_move(
                "TEST-123", "NEWQUEUE", auth=yandex_auth_cloud
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
