from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.queues import Queue
from tests.aioresponses_utils import RequestCapture


class TestQueueCreate:
    async def test_success(
        self, tracker_client: TrackerClient, sample_queue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_queue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/queues/",
                callback=capture.callback,
            )

            result = await tracker_client.queue_create(
                key="TRASH",
                name="Trash",
                lead="ivan",
                issue_types_config=[
                    {"issueType": "task", "workflow": "W1", "resolutions": ["wontFix"]}
                ],
            )

            assert isinstance(result, Queue)

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "key": "TRASH",
                "name": "Trash",
                "lead": "ivan",
                "defaultType": "task",
                "defaultPriority": "normal",
                "issueTypesConfig": [
                    {"issueType": "task", "workflow": "W1", "resolutions": ["wontFix"]}
                ],
            }
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_queue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_queue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/queues/",
                callback=capture.callback,
            )

            await tracker_client_no_org.queue_create(
                key="TRASH", name="Trash", lead="ivan", auth=yandex_auth_cloud
            )

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {"Authorization": "OAuth auth-token", "X-Cloud-Org-ID": "cloud-org"}
        )
