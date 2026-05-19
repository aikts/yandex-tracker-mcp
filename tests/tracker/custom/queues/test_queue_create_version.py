from datetime import date
from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.queues import QueueVersion
from tests.aioresponses_utils import RequestCapture


class TestQueueCreateVersion:
    async def test_success_required_fields(
        self, tracker_client: TrackerClient, sample_version_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=[sample_version_data])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/versions/",
                callback=capture.callback,
            )

            result = await tracker_client.queue_create_version(
                "TEST",
                name="1.0.0",
            )

            assert isinstance(result, QueueVersion)
            assert result.name == "1.0.0"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"queue": "TEST", "name": "1.0.0"})

    async def test_success_optional_fields(
        self, tracker_client: TrackerClient, sample_version_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=[sample_version_data])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/versions/",
                callback=capture.callback,
            )

            result = await tracker_client.queue_create_version(
                "TEST",
                name="1.0.0",
                description="Initial release",
                start_date=date(2023, 1, 1),
                due_date=date(2023, 12, 31),
            )

            assert isinstance(result, QueueVersion)
            assert result.description == "Initial release"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "name": "1.0.0",
                "description": "Initial release",
                "startDate": "2023-01-01",
                "dueDate": "2023-12-31",
            }
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_version_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_version_data])

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/versions/",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.queue_create_version(
                "PROJ",
                name="1.0.0",
                auth=yandex_auth_cloud,
            )

            assert isinstance(result, QueueVersion)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
        capture.last_request.assert_json_body({"queue": "PROJ", "name": "1.0.0"})
