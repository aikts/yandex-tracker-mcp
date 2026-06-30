from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestEntityDelete:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/entities/project/ent-123",
                callback=capture.callback,
            )

            await tracker_client.entity_delete("project", "ent-123")

        capture.assert_called_once()

    async def test_with_board(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/entities/project/ent-123?withBoard=true",
                callback=capture.callback,
            )

            await tracker_client.entity_delete("project", "ent-123", with_board=True)

        capture.assert_called_once()
        capture.last_request.assert_param("withBoard", "true")

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/entities/goal/g-1",
                callback=capture.callback,
            )

            await tracker_client_no_org.entity_delete(
                "goal", "g-1", auth=yandex_auth_cloud
            )

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
