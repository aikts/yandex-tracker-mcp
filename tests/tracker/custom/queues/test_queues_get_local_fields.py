from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import LocalField
from tests.aioresponses_utils import RequestCapture


class TestQueuesGetLocalFields:
    async def test_success(
        self, tracker_client: TrackerClient, sample_local_field_data: dict[str, Any]
    ) -> None:
        fields_response = [sample_local_field_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/localFields",
                payload=fields_response,
            )

            result = await tracker_client.queues_get_local_fields("TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], LocalField)
            assert result[0].key == "customField1"

    async def test_with_auth(
        self,
        tracker_client: TrackerClient,
        sample_local_field_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        fields_response = [sample_local_field_data]
        capture = RequestCapture(payload=fields_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/PROJ/localFields",
                callback=capture.callback,
            )

            result = await tracker_client.queues_get_local_fields(
                "PROJ", auth=yandex_auth
            )

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
