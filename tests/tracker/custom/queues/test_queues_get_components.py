from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.components import Component
from tests.aioresponses_utils import RequestCapture

URL = "https://api.tracker.yandex.net/v3/queues/AP/components"


class TestQueuesGetComponents:
    async def test_success(
        self, tracker_client: TrackerClient, sample_component_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=[sample_component_data])

        with aioresponses() as m:
            m.get(URL, callback=capture.callback)

            result = await tracker_client.queues_get_components("AP")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Component)
            assert result[0].id == 856
            assert result[0].version == 1
            assert result[0].name == "Design"
            assert result[0].assign_auto is False
            assert result[0].queue is not None
            assert result[0].queue.key == "AP"
            assert result[0].lead is not None
            assert result[0].lead.id == "i.ivanov"

        capture.assert_called_once()
        assert capture.last_request.url.path == "/v3/queues/AP/components"
        # The queue-scoped path takes no `perPage` / `page`: it is not paginated.
        assert not capture.last_request.url.query

    async def test_multiple(
        self,
        tracker_client: TrackerClient,
        sample_component_data: dict[str, Any],
        sample_bare_component_data: dict[str, Any],
    ) -> None:
        with aioresponses() as m:
            m.get(URL, payload=[sample_component_data, sample_bare_component_data])

            result = await tracker_client.queues_get_components("AP")

        assert [c.id for c in result] == [856, 857]
        assert result[1].description is None
        assert result[1].lead is None

    async def test_empty(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/NOCOMPONENTS/components",
                payload=[],
            )

            result = await tracker_client.queues_get_components("NOCOMPONENTS")

        assert result == []

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_component_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_component_data])

        with aioresponses() as m:
            m.get(URL, callback=capture.callback)

            result = await tracker_client_no_org.queues_get_components(
                "AP", auth=yandex_auth_cloud
            )

            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
