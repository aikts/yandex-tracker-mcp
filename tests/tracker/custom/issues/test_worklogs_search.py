from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import Worklog
from tests.aioresponses_utils import RequestCapture


class TestWorklogsSearch:
    async def test_success_no_filters(self, tracker_client: TrackerClient) -> None:
        worklog_data = {
            "self": "https://api.tracker.yandex.net/v3/worklog/1",
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
            "createdAt": "2024-01-15T10:00:00.000+0000",
            "duration": "PT4H",
        }
        worklogs_response = [worklog_data]

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                payload=worklogs_response,
            )

            result = await tracker_client.worklogs_search()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Worklog)
            assert result[0].comment == "Work done on the issue"

    async def test_with_created_by_filter(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search(created_by="john.doe")

        capture.assert_called_once()
        capture.last_request.assert_json_field("createdBy", "john.doe")

    async def test_with_created_at_from_only(
        self, tracker_client: TrackerClient
    ) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search(
                created_at_from="2024-01-01T00:00:00.000+0000"
            )

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["createdAt"]["from"] == "2024-01-01T00:00:00.000+0000"
        assert "to" not in body["createdAt"]

    async def test_with_created_at_to_only(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search(
                created_at_to="2024-12-31T23:59:59.999+0000"
            )

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert "from" not in body["createdAt"]
        assert body["createdAt"]["to"] == "2024-12-31T23:59:59.999+0000"

    async def test_with_date_range_filter(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search(
                created_at_from="2024-01-01T00:00:00.000+0000",
                created_at_to="2024-12-31T23:59:59.999+0000",
            )

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["createdAt"]["from"] == "2024-01-01T00:00:00.000+0000"
        assert body["createdAt"]["to"] == "2024-12-31T23:59:59.999+0000"

    async def test_with_all_filters(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search(
                created_by="john.doe",
                created_at_from="2024-01-01T00:00:00.000+0000",
                created_at_to="2024-12-31T23:59:59.999+0000",
            )

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["createdBy"] == "john.doe"
        assert body["createdAt"]["from"] == "2024-01-01T00:00:00.000+0000"
        assert body["createdAt"]["to"] == "2024-12-31T23:59:59.999+0000"

    async def test_with_auth(
        self, tracker_client: TrackerClient, yandex_auth: YandexAuth
    ) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search(auth=yandex_auth)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_empty_body_when_no_filters(
        self, tracker_client: TrackerClient
    ) -> None:
        capture = RequestCapture(payload=[])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/worklog/_search",
                callback=capture.callback,
            )

            await tracker_client.worklogs_search()

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body == {}
