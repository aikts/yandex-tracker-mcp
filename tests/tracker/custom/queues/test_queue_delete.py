from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestQueueDelete:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/queues/TRASH",
                callback=capture.callback,
            )

            await tracker_client.queue_delete("TRASH")

        capture.assert_called_once()

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/queues/TRASH",
                callback=capture.callback,
            )

            await tracker_client_no_org.queue_delete("TRASH", auth=yandex_auth_cloud)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {"Authorization": "OAuth auth-token", "X-Cloud-Org-ID": "cloud-org"}
        )
