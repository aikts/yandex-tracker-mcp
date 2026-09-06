from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture

URL = "https://api.tracker.yandex.net/v3/components/856"


class TestComponentDelete:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(URL, callback=capture.callback)

            await tracker_client.component_delete(856)

        capture.assert_called_once()
        assert capture.last_request.url.path == "/v3/components/856"
        # No `version` on delete, and no body.
        assert "version" not in capture.last_request.url.query
        assert capture.last_request.json_data is None

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(URL, callback=capture.callback)

            await tracker_client_no_org.component_delete(856, auth=yandex_auth_cloud)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
