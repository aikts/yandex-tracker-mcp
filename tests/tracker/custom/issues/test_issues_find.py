from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


class TestIssuesFind:
    async def test_success(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        search_response = [sample_issue_data]

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                payload=search_response,
            )

            result = await tracker_client.issues_find("Queue: TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Issue)
            assert result[0].key == "TEST-123"

    async def test_with_pagination(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        search_response = [sample_issue_data]
        capture = RequestCapture(payload=search_response)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=2&perPage=50",
                callback=capture.callback,
            )

            result = await tracker_client.issues_find(
                "Queue: TEST", per_page=50, page=2
            )

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_params({"perPage": 50, "page": 2})
        capture.last_request.assert_json_field("query", "Queue: TEST")
