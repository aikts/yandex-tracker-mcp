from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import Entity
from tests.aioresponses_utils import RequestCapture


class TestEntityCreate:
    async def test_success_required_fields(
        self, tracker_client: TrackerClient, sample_entity_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entity_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/project",
                callback=capture.callback,
            )

            result = await tracker_client.entity_create(
                "project",
                summary="Test Project",
            )

            assert isinstance(result, Entity)
            assert result.id == "6a43e17349b4e74442327d7f"
            assert result.shortId == 22
            assert result.entityType == "project"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"fields": {"summary": "Test Project"}})

    async def test_success_with_extra_fields(
        self, tracker_client: TrackerClient, sample_entity_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entity_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/goal",
                callback=capture.callback,
            )

            result = await tracker_client.entity_create(
                "goal",
                summary="Q1 Goal",
                fields={"lead": "j.doe", "end": "2026-03-01"},
            )

            assert isinstance(result, Entity)

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"fields": {"summary": "Q1 Goal", "lead": "j.doe", "end": "2026-03-01"}}
        )

    async def test_extra_fields_do_not_override_summary(
        self, tracker_client: TrackerClient, sample_entity_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_entity_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/project",
                callback=capture.callback,
            )

            await tracker_client.entity_create(
                "project",
                summary="Real Summary",
                fields={"summary": "Ignored", "lead": "j.doe"},
            )

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"fields": {"summary": "Real Summary", "lead": "j.doe"}}
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_entity_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_entity_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/entities/portfolio",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.entity_create(
                "portfolio",
                summary="Portfolio A",
                auth=yandex_auth_cloud,
            )

            assert isinstance(result, Entity)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
        capture.last_request.assert_json_body({"fields": {"summary": "Portfolio A"}})
