from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import Entity
from tests.aioresponses_utils import RequestCapture


class TestEntityGet:
    async def test_success(
        self, tracker_client: TrackerClient, sample_entity_full: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/entities/project/655f328da834c7631234abcd",
                payload=sample_entity_full,
            )

            result = await tracker_client.entity_get(
                "project", "655f328da834c7631234abcd"
            )

            assert isinstance(result, Entity)
            assert result.id == "655f328da834c7631234abcd"
            assert result.shortId == 2
            assert result.entityType == "project"
            assert result.fields is not None
            assert result.fields["summary"] == "Test Project"
            assert result.createdBy is not None
            assert result.createdBy.display == "Test User"

    async def test_with_fields_and_expand(
        self, tracker_client: TrackerClient, sample_entity_full: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entity_full)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/entities/goal/g-1?expand=attachments&fields=summary,description",
                callback=capture.callback,
            )

            await tracker_client.entity_get(
                "goal", "g-1", fields="summary,description", expand_attachments=True
            )

        capture.assert_called_once()
        capture.last_request.assert_params(
            {"fields": "summary,description", "expand": "attachments"}
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_entity_full: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_entity_full)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/entities/project/p-1",
                callback=capture.callback,
            )

            await tracker_client_no_org.entity_get(
                "project", "p-1", auth=yandex_auth_cloud
            )

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {"Authorization": "OAuth auth-token", "X-Cloud-Org-ID": "cloud-org"}
        )
