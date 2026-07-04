from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestComponentsList:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        components_response = [
            {
                "self": "https://api.tracker.yandex.net/v3/components/111175",
                "id": 111175,
                "version": 1,
                "name": "Test",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                    "id": "12345",
                    "key": "TEST",
                    "display": "Test Queue",
                },
                "assignAuto": False,
            },
            {
                "self": "https://api.tracker.yandex.net/v3/components/111176",
                "id": 111176,
                "version": 1,
                "name": "Monitoring",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/OTHER",
                    "id": "67890",
                    "key": "OTHER",
                    "display": "Other Queue",
                },
                "assignAuto": False,
            },
        ]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components?page=1&perPage=50",
                payload=components_response,
                status=200,
            )

            result = await tracker_client.components_list()

            assert len(result) == 2
            assert result[0].name == "Test"
            assert result[0].queue is not None
            assert result[0].queue.key == "TEST"
            assert result[1].queue is not None
            assert result[1].queue.key == "OTHER"

    async def test_with_pagination(self, tracker_client: TrackerClient) -> None:
        components_response = [
            {
                "self": "https://api.tracker.yandex.net/v3/components/111175",
                "id": 111175,
                "version": 1,
                "name": "Test",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                    "id": "12345",
                    "key": "TEST",
                    "display": "Test Queue",
                },
                "assignAuto": False,
            }
        ]
        capture = RequestCapture(payload=components_response, status=200)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components?page=2&perPage=10",
                callback=capture.callback,
            )

            result = await tracker_client.components_list(per_page=10, page=2)

            assert len(result) == 1
            assert result[0].name == "Test"

        capture.assert_called_once()
        capture.last_request.assert_param("perPage", 10)
        capture.last_request.assert_param("page", 2)

    async def test_with_auth(
        self, tracker_client: TrackerClient, yandex_auth: YandexAuth
    ) -> None:
        components_response = [
            {
                "self": "https://api.tracker.yandex.net/v3/components/111177",
                "id": 111177,
                "version": 1,
                "name": "AuthTest",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/AUTH",
                    "id": "999",
                    "key": "AUTH",
                    "display": "Auth Queue",
                },
                "assignAuto": False,
            }
        ]
        capture = RequestCapture(payload=components_response, status=200)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components?page=1&perPage=50",
                callback=capture.callback,
            )

            result = await tracker_client.components_list(auth=yandex_auth)

            assert len(result) == 1
            assert result[0].name == "AuthTest"

        capture.assert_called_once()
        capture.last_request.assert_param("perPage", 50)
        capture.last_request.assert_param("page", 1)
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
