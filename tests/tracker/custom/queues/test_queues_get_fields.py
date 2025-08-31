from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import GlobalField
from tests.aioresponses_utils import RequestCapture


class TestQueuesGetFields:
    async def test_success(
        self, tracker_client: TrackerClient, sample_global_field_data: dict[str, Any]
    ) -> None:
        fields_response = [sample_global_field_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/fields",
                payload=fields_response,
            )

            result = await tracker_client.queues_get_fields("TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], GlobalField)
            assert result[0].key == "summary"

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_global_field_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        fields_response = [sample_global_field_data]
        capture = RequestCapture(payload=fields_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/PROJ/fields",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.queues_get_fields(
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
        fields_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/EMPTY/fields",
                payload=fields_response,
            )

            result = await tracker_client.queues_get_fields("EMPTY")

            assert isinstance(result, list)
            assert len(result) == 0
