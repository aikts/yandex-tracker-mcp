from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import Entity
from tests.aioresponses_utils import RequestCapture


class TestEntityUpdate:
    async def test_link_to_portfolio(
        self, tracker_client: TrackerClient, sample_entity_full: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entity_full)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/entities/project/p-1",
                callback=capture.callback,
            )

            result = await tracker_client.entity_update(
                "project",
                "p-1",
                fields={"parentEntity": {"primary": "portf-1"}},
            )

            assert isinstance(result, Entity)

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"fields": {"parentEntity": {"primary": "portf-1"}}}
        )

    async def test_update_with_comment_and_links(
        self, tracker_client: TrackerClient, sample_entity_full: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entity_full)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/entities/project/p-1",
                callback=capture.callback,
            )

            await tracker_client.entity_update(
                "project",
                "p-1",
                fields={"summary": "Renamed"},
                comment="linked to goal",
                links=[{"relationship": "works towards", "entity": "goal-1"}],
            )

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "fields": {"summary": "Renamed"},
                "comment": "linked to goal",
                "links": [{"relationship": "works towards", "entity": "goal-1"}],
            }
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_entity_full: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_entity_full)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/entities/goal/g-1",
                callback=capture.callback,
            )

            await tracker_client_no_org.entity_update(
                "goal", "g-1", fields={"summary": "G"}, auth=yandex_auth_cloud
            )

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {"Authorization": "OAuth auth-token", "X-Cloud-Org-ID": "cloud-org"}
        )
