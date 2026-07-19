from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestComponentCreate:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        component_response = {
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

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/components",
                payload=component_response,
                status=201,
            )

            result = await tracker_client.component_create("TEST", name="Test")

            assert result.name == "Test"
            assert result.id == 111175

    async def test_with_description(self, tracker_client: TrackerClient) -> None:
        component_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111176",
            "id": 111176,
            "version": 1,
            "name": "Monitoring",
            "description": "System monitoring",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "12345",
                "key": "TEST",
                "display": "Test Queue",
            },
            "assignAuto": False,
        }
        capture = RequestCapture(payload=component_response, status=201)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/components",
                callback=capture.callback,
            )

            result = await tracker_client.component_create(
                "TEST", name="Monitoring", description="System monitoring"
            )

            assert result.name == "Monitoring"
            assert result.description == "System monitoring"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "name": "Monitoring",
                "queue": "TEST",
                "description": "System monitoring",
            }
        )

    async def test_with_lead_and_assign_auto(
        self, tracker_client: TrackerClient
    ) -> None:
        component_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111178",
            "id": 111178,
            "version": 1,
            "name": "LeadTest",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "12345",
                "key": "TEST",
                "display": "Test Queue",
            },
            "lead": {
                "self": "https://api.tracker.yandex.net/v3/users/123",
                "id": "123",
                "display": "Test User",
            },
            "assignAuto": True,
        }
        capture = RequestCapture(payload=component_response, status=201)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/components",
                callback=capture.callback,
            )

            result = await tracker_client.component_create(
                "TEST",
                name="LeadTest",
                lead="testuser",
                assign_auto=True,
            )

            assert result.name == "LeadTest"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "name": "LeadTest",
                "queue": "TEST",
                "lead": "testuser",
                "assignAuto": True,
            }
        )

    async def test_with_auth(
        self, tracker_client: TrackerClient, yandex_auth: YandexAuth
    ) -> None:
        component_response = {
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
        capture = RequestCapture(payload=component_response, status=201)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/components",
                callback=capture.callback,
            )

            result = await tracker_client.component_create(
                "AUTH", name="AuthTest", auth=yandex_auth
            )

            assert result.name == "AuthTest"

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
        capture.last_request.assert_json_body(
            {
                "name": "AuthTest",
                "queue": "AUTH",
            }
        )
