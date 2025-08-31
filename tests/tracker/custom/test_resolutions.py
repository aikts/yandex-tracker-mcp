from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from tests.aioresponses_utils import RequestCapture


class TestResolutions:
    @pytest.fixture
    def sample_resolution_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/resolutions/1",
            "id": 1,
            "version": 1,
            "key": "fixed",
            "name": "Fixed",
            "description": "Issue has been fixed",
            "order": 1,
        }

    async def test_get_resolutions_success(
        self, tracker_client: TrackerClient, sample_resolution_data: dict[str, Any]
    ) -> None:
        resolutions_response = [sample_resolution_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/resolutions",
                payload=resolutions_response,
            )

            result = await tracker_client.get_resolutions()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Resolution)
            assert result[0].key == "fixed"
            assert result[0].name == "Fixed"
            assert result[0].description == "Issue has been fixed"
            assert result[0].order == 1

    async def test_get_resolutions_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_resolution_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        resolutions_response = [sample_resolution_data]
        capture = RequestCapture(payload=resolutions_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/resolutions",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.get_resolutions(auth=yandex_auth_cloud)

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_get_resolutions_multiple(
        self, tracker_client: TrackerClient
    ) -> None:
        resolution1_data = {
            "self": "https://api.tracker.yandex.net/v3/resolutions/1",
            "id": 1,
            "version": 1,
            "key": "fixed",
            "name": "Fixed",
            "description": "Issue has been fixed",
            "order": 1,
        }

        resolution2_data = {
            "self": "https://api.tracker.yandex.net/v3/resolutions/2",
            "id": 2,
            "version": 1,
            "key": "wontFix",
            "name": "Won't Fix",
            "description": "Issue will not be fixed",
            "order": 2,
        }

        resolution3_data = {
            "self": "https://api.tracker.yandex.net/v3/resolutions/3",
            "id": 3,
            "version": 1,
            "key": "duplicate",
            "name": "Duplicate",
            "description": "Issue is a duplicate",
            "order": 3,
        }

        resolutions_response = [resolution1_data, resolution2_data, resolution3_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/resolutions",
                payload=resolutions_response,
            )

            result = await tracker_client.get_resolutions()

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(resolution, Resolution) for resolution in result)

            assert result[0].key == "fixed"
            assert result[0].order == 1
            assert result[1].key == "wontFix"
            assert result[1].order == 2
            assert result[2].key == "duplicate"
            assert result[2].order == 3

    async def test_get_resolutions_empty(self, tracker_client: TrackerClient) -> None:
        resolutions_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/resolutions",
                payload=resolutions_response,
            )

            result = await tracker_client.get_resolutions()

            assert isinstance(result, list)
            assert len(result) == 0
