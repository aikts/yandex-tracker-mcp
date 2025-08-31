from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.queues import QueueVersion
from tests.aioresponses_utils import RequestCapture


class TestQueuesGetVersions:
    async def test_success(
        self, tracker_client: TrackerClient, sample_version_data: dict[str, Any]
    ) -> None:
        versions_response = [sample_version_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/versions",
                payload=versions_response,
            )

            result = await tracker_client.queues_get_versions("TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], QueueVersion)
            assert result[0].name == "1.0.0"
            assert result[0].description == "Initial release"
            assert result[0].released is False
            assert result[0].archived is False

    async def test_multiple(self, tracker_client: TrackerClient) -> None:
        version1_data = {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST/versions/1",
            "id": 123,
            "version": 1,
            "name": "1.0.0",
            "description": "Initial release",
            "startDate": "2023-01-01",
            "dueDate": "2023-06-30",
            "released": True,
            "archived": False,
        }

        version2_data = {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST/versions/2",
            "id": 456,
            "version": 2,
            "name": "2.0.0",
            "description": "Major update",
            "startDate": "2023-07-01",
            "dueDate": "2023-12-31",
            "released": False,
            "archived": False,
        }

        versions_response = [version1_data, version2_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/versions",
                payload=versions_response,
            )

            result = await tracker_client.queues_get_versions("TEST")

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(version, QueueVersion) for version in result)

            # Check first version
            assert result[0].name == "1.0.0"
            assert result[0].released is True

            # Check second version
            assert result[1].name == "2.0.0"
            assert result[1].released is False

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_version_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        versions_response = [sample_version_data]
        capture = RequestCapture(payload=versions_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/PROJ/versions",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.queues_get_versions(
                "PROJ", auth=yandex_auth_cloud
            )

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_empty(self, tracker_client: TrackerClient) -> None:
        versions_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/NOVERSIONS/versions",
                payload=versions_response,
            )

            result = await tracker_client.queues_get_versions("NOVERSIONS")

            assert isinstance(result, list)
            assert len(result) == 0
