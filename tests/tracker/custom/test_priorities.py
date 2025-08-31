from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.priorities import Priority
from tests.aioresponses_utils import RequestCapture


class TestPriorities:
    @pytest.fixture
    def sample_priority_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "version": 1,
            "key": "normal",
            "name": "Normal",
            "order": 2,
        }

    async def test_get_priorities_success(
        self, tracker_client: TrackerClient, sample_priority_data: dict[str, Any]
    ) -> None:
        priorities_response = [sample_priority_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await tracker_client.get_priorities()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Priority)
            assert result[0].key == "normal"
            assert result[0].name == "Normal"
            assert result[0].order == 2

    async def test_get_priorities_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_priority_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        priorities_response = [sample_priority_data]
        capture = RequestCapture(payload=priorities_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.get_priorities(auth=yandex_auth)

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_get_priorities_multiple_with_order(
        self, tracker_client: TrackerClient
    ) -> None:
        priority1_data = {
            "self": "https://api.tracker.yandex.net/v3/priorities/1",
            "id": "1",
            "version": 1,
            "key": "trivial",
            "name": "Trivial",
            "order": 1,
        }

        priority2_data = {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "version": 1,
            "key": "normal",
            "name": "Normal",
            "order": 2,
        }

        priority3_data = {
            "self": "https://api.tracker.yandex.net/v3/priorities/3",
            "id": "3",
            "version": 1,
            "key": "critical",
            "name": "Critical",
            "order": 3,
        }

        priorities_response = [priority1_data, priority2_data, priority3_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await tracker_client.get_priorities()

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(priority, Priority) for priority in result)

            # Check priorities in order
            assert result[0].key == "trivial"
            assert result[0].order == 1
            assert result[1].key == "normal"
            assert result[1].order == 2
            assert result[2].key == "critical"
            assert result[2].order == 3

    async def test_get_priorities_empty(self, tracker_client: TrackerClient) -> None:
        priorities_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await tracker_client.get_priorities()

            assert isinstance(result, list)
            assert len(result) == 0
