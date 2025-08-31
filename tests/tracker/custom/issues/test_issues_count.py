from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestIssuesCount:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(body="42")

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_count",
                callback=capture.callback,
            )

            result = await tracker_client.issues_count("Queue: TEST")

            assert result == 42

        capture.assert_called_once()
        capture.last_request.assert_json_field("query", "Queue: TEST")

    async def test_with_auth(
        self, tracker_client_no_org: TrackerClient, yandex_auth_cloud: YandexAuth
    ) -> None:
        capture = RequestCapture(body="10")

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_count",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issues_count(
                "Status: Open", auth=yandex_auth_cloud
            )

            assert result == 10

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
