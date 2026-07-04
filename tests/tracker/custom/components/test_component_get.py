from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestComponentGet:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        component_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111175",
            "id": 111175,
            "version": 2,
            "name": "Test Component",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "12345",
                "key": "TEST",
                "display": "Test Queue",
            },
            "assignAuto": False,
        }

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components/111175",
                payload=component_response,
                status=200,
            )

            result = await tracker_client.component_get(111175)

            assert result.id == 111175
            assert result.version == 2
            assert result.name == "Test Component"

    async def test_with_auth(
        self, tracker_client: TrackerClient, yandex_auth: YandexAuth
    ) -> None:
        component_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111177",
            "id": 111177,
            "version": 3,
            "name": "Auth Component",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/AUTH",
                "id": "999",
                "key": "AUTH",
                "display": "Auth Queue",
            },
            "assignAuto": False,
        }
        capture = RequestCapture(payload=component_response, status=200)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components/111177",
                callback=capture.callback,
            )

            result = await tracker_client.component_get(111177, auth=yandex_auth)

            assert result.id == 111177
            assert result.version == 3

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
