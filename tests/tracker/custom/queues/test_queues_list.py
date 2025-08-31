from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.queues import Queue
from tests.aioresponses_utils import RequestCapture


class TestQueuesList:
    async def test_success(
        self, tracker_client: TrackerClient, sample_queue_data: dict[str, Any]
    ) -> None:
        queues_response = [sample_queue_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues?page=1&perPage=100",
                payload=queues_response,
            )

            result = await tracker_client.queues_list()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Queue)
            assert result[0].key == "TEST"
            assert result[0].name == "Test Queue"
            assert result[0].description == "A test queue for testing purposes"

    async def test_with_pagination(
        self, tracker_client: TrackerClient, sample_queue_data: dict[str, Any]
    ) -> None:
        queues_response = [sample_queue_data]
        capture = RequestCapture(payload=queues_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues?page=2&perPage=50",
                callback=capture.callback,
            )

            result = await tracker_client.queues_list(per_page=50, page=2)

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_params({"perPage": 50, "page": 2})

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_queue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        queues_response = [sample_queue_data]
        capture = RequestCapture(payload=queues_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues?page=1&perPage=100",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.queues_list(auth=yandex_auth_cloud)

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
