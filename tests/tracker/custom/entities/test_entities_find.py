from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import Entity
from tests.aioresponses_utils import RequestCapture


class TestEntitiesFind:
    async def test_success(
        self, tracker_client: TrackerClient, sample_entities_search: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entities_search)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/project/_search?page=1&perPage=50",
                callback=capture.callback,
            )

            result = await tracker_client.entities_find("project")

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(e, Entity) for e in result)
            assert result[0].shortId == 2

        capture.assert_called_once()
        capture.last_request.assert_json_body({})

    async def test_with_filter_and_pagination(
        self, tracker_client: TrackerClient, sample_entities_search: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entities_search)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/goal/_search?page=2&perPage=10",
                callback=capture.callback,
            )

            await tracker_client.entities_find(
                "goal",
                input="Q1",
                filter={"entityStatus": "in_progress"},
                order_by="summary",
                per_page=10,
                page=2,
            )

        capture.assert_called_once()
        capture.last_request.assert_params({"perPage": 10, "page": 2})
        capture.last_request.assert_json_body(
            {
                "input": "Q1",
                "filter": {"entityStatus": "in_progress"},
                "orderBy": "summary",
            }
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_entities_search: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_entities_search)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/portfolio/_search?page=1&perPage=50",
                callback=capture.callback,
            )

            await tracker_client_no_org.entities_find(
                "portfolio", auth=yandex_auth_cloud
            )

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {"Authorization": "OAuth auth-token", "X-Cloud-Org-ID": "cloud-org"}
        )
