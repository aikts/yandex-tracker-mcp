from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.queues import Queue
from tests.aioresponses_utils import RequestCapture


class TestQueueGet:
    async def test_success(
        self, tracker_client: TrackerClient, sample_queue_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST",
                payload=sample_queue_data,
            )

            result = await tracker_client.queue_get("TEST")

            assert isinstance(result, Queue)
            # Basic fields
            assert result.id == 123
            assert result.key == "TEST"
            assert result.name == "Test Queue"
            assert result.description == "A test queue for testing purposes"

            # Default type reference
            assert result.defaultType is not None
            assert result.defaultType.id == "1"
            assert result.defaultType.key == "task"
            assert result.defaultType.display == "Task"

            # Default priority reference
            assert result.defaultPriority is not None
            assert result.defaultPriority.id == "2"
            assert result.defaultPriority.key == "normal"
            assert result.defaultPriority.display == "Normal"

    async def test_with_expand(
        self, tracker_client: TrackerClient, sample_queue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_queue_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST?expand=all",
                callback=capture.callback,
            )

            result = await tracker_client.queue_get("TEST", expand=["all"])

            assert isinstance(result, Queue)
            assert result.key == "TEST"

        capture.assert_called_once()
        capture.last_request.assert_params({"expand": "all"})

    async def test_with_multiple_expand(
        self, tracker_client: TrackerClient, sample_queue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_queue_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST?expand=workflows%2Cfields",
                callback=capture.callback,
            )

            result = await tracker_client.queue_get(
                "TEST", expand=["workflows", "fields"]
            )

            assert isinstance(result, Queue)
            assert result.key == "TEST"

        capture.assert_called_once()
        capture.last_request.assert_params({"expand": "workflows,fields"})

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_queue_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_queue_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/PROJ",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.queue_get("PROJ", auth=yandex_auth)

            assert isinstance(result, Queue)
            assert result.key == "TEST"

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
