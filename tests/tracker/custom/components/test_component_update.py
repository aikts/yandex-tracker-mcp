import re

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


class TestComponentUpdate:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        get_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111175",
            "id": 111175,
            "version": 2,
            "name": "Old Name",
            "description": "Old description",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "12345",
                "key": "TEST",
                "display": "Test Queue",
            },
            "assignAuto": False,
        }
        patch_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111175",
            "id": 111175,
            "version": 3,
            "name": "Updated",
            "description": "Updated description",
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
                payload=get_response,
                status=200,
            )
            m.patch(
                re.compile(r"https://api\.tracker\.yandex\.net/v3/components/111175\?.*"),
                payload=patch_response,
                status=200,
            )

            result = await tracker_client.component_update(
                111175, name="Updated", description="Updated description"
            )

            assert result.name == "Updated"
            assert result.description == "Updated description"
            assert result.id == 111175

    async def test_name_only(self, tracker_client: TrackerClient) -> None:
        get_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111175",
            "id": 111175,
            "version": 2,
            "name": "Old Name",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "12345",
                "key": "TEST",
                "display": "Test Queue",
            },
            "assignAuto": False,
        }
        patch_capture = RequestCapture(
            payload={
                "self": "https://api.tracker.yandex.net/v3/components/111175",
                "id": 111175,
                "version": 3,
                "name": "OnlyName",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                    "id": "12345",
                    "key": "TEST",
                    "display": "Test Queue",
                },
                "assignAuto": False,
            },
            status=200,
        )

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components/111175",
                payload=get_response,
                status=200,
            )
            m.patch(
                re.compile(r"https://api\.tracker\.yandex\.net/v3/components/111175\?.*"),
                callback=patch_capture.callback,
            )

            result = await tracker_client.component_update(111175, name="OnlyName")

            assert result.name == "OnlyName"

        patch_capture.assert_called_once()
        patch_capture.last_request.assert_json_body({"name": "OnlyName"})
        patch_capture.last_request.assert_param("version", 2)

    async def test_with_lead(
        self, tracker_client: TrackerClient
    ) -> None:
        get_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111178",
            "id": 111178,
            "version": 2,
            "name": "Old Name",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "12345",
                "key": "TEST",
                "display": "Test Queue",
            },
            "assignAuto": False,
        }
        patch_capture = RequestCapture(
            payload={
                "self": "https://api.tracker.yandex.net/v3/components/111178",
                "id": 111178,
                "version": 3,
                "name": "LeadUpdate",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                    "id": "12345",
                    "key": "TEST",
                    "display": "Test Queue",
                },
                "assignAuto": False,
            },
            status=200,
        )

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components/111178",
                payload=get_response,
                status=200,
            )
            m.patch(
                re.compile(r"https://api\.tracker\.yandex\.net/v3/components/111178\?.*"),
                callback=patch_capture.callback,
            )

            result = await tracker_client.component_update(
                111178, name="LeadUpdate", lead="newlead"
            )

            assert result.name == "LeadUpdate"

        patch_capture.assert_called_once()
        patch_capture.last_request.assert_param("version", 2)
        patch_capture.last_request.assert_json_body(
            {"name": "LeadUpdate", "lead": "newlead"}
        )

    async def test_with_auth(
        self, tracker_client: TrackerClient, yandex_auth: YandexAuth
    ) -> None:
        get_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111177",
            "id": 111177,
            "version": 5,
            "name": "Old Auth",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/AUTH",
                "id": "999",
                "key": "AUTH",
                "display": "Auth Queue",
            },
            "assignAuto": False,
        }
        patch_capture = RequestCapture(
            payload={
                "self": "https://api.tracker.yandex.net/v3/components/111177",
                "id": 111177,
                "version": 6,
                "name": "AuthUpdate",
                "queue": {
                    "self": "https://api.tracker.yandex.net/v3/queues/AUTH",
                    "id": "999",
                    "key": "AUTH",
                    "display": "Auth Queue",
                },
                "assignAuto": False,
            },
            status=200,
        )

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components/111177",
                payload=get_response,
                status=200,
            )
            m.patch(
                re.compile(r"https://api\.tracker\.yandex\.net/v3/components/111177\?.*"),
                callback=patch_capture.callback,
            )

            result = await tracker_client.component_update(
                111177, name="AuthUpdate", auth=yandex_auth
            )

            assert result.name == "AuthUpdate"

        patch_capture.assert_called_once()
        patch_capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
        patch_capture.last_request.assert_param("version", 5)
        patch_capture.last_request.assert_json_body({"name": "AuthUpdate"})

    async def test_missing_version_raises(self, tracker_client: TrackerClient) -> None:
        get_response = {
            "self": "https://api.tracker.yandex.net/v3/components/111175",
            "id": 111175,
            "name": "No Version",
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
                payload=get_response,
                status=200,
            )

            try:
                await tracker_client.component_update(111175, name="Should Fail")
                assert False, "Expected ValueError"
            except ValueError as e:
                assert "version is missing" in str(e)
