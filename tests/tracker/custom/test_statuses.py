from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.statuses import Status
from tests.aioresponses_utils import RequestCapture


class TestStatuses:
    @pytest.fixture
    def sample_status_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "version": 1,
            "key": "open",
            "name": "Open",
            "order": 1,
            "type": "new",
            "statusType": {
                "self": "https://api.tracker.yandex.net/v3/statusTypes/1",
                "id": "1",
                "key": "new",
                "display": "New",
            },
        }

    async def test_get_statuses_success(
        self, tracker_client: TrackerClient, sample_status_data: dict[str, Any]
    ) -> None:
        statuses_response = [sample_status_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/statuses", payload=statuses_response
            )

            result = await tracker_client.get_statuses()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Status)
            assert result[0].key == "open"
            assert result[0].name == "Open"

    async def test_get_statuses_with_auth(
        self,
        tracker_client: TrackerClient,
        sample_status_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        statuses_response = [sample_status_data]
        capture = RequestCapture(payload=statuses_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/statuses", callback=capture.callback
            )

            result = await tracker_client.get_statuses(auth=yandex_auth)

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_get_statuses_empty(self, tracker_client: TrackerClient) -> None:
        statuses_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/statuses", payload=statuses_response
            )

            result = await tracker_client.get_statuses()

            assert isinstance(result, list)
            assert len(result) == 0
