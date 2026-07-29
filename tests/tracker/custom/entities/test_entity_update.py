import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.entities import (
    GoalEntity,
    PortfolioEntity,
    ProjectEntity,
)
from tests.aioresponses_utils import RequestCapture

ENTITY_UPDATE_CASES = [
    ("project", "project_update", "sample_project_data", ProjectEntity),
    ("portfolio", "portfolio_update", "sample_portfolio_data", PortfolioEntity),
    ("goal", "goal_update", "sample_goal_data", GoalEntity),
]


class TestEntityUpdate:
    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_UPDATE_CASES
    )
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        model_cls: type,
        request: pytest.FixtureRequest,
    ) -> None:
        entity_data: dict[str, Any] = request.getfixturevalue(fixture_name)
        capture = RequestCapture(payload=entity_data)

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            result = await method(entity_data["id"], summary="Updated Summary")

            assert isinstance(result, model_cls)
            assert result.id == entity_data["id"]  # type: ignore[attr-defined]

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"fields": {"summary": "Updated Summary"}}
        )

    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_UPDATE_CASES
    )
    async def test_passes_version_and_comment(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        model_cls: type,
        request: pytest.FixtureRequest,
    ) -> None:
        entity_data: dict[str, Any] = request.getfixturevalue(fixture_name)
        capture = RequestCapture(payload=entity_data)

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            await method(
                entity_data["id"],
                entity_status="cancelled",
                comment="closing this out",
                version=3,
            )

        capture.assert_called_once()
        capture.last_request.assert_params({"version": 3})
        capture.last_request.assert_json_body(
            {
                "fields": {"entityStatus": "cancelled"},
                "comment": "closing this out",
            }
        )

    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_UPDATE_CASES
    )
    async def test_no_optional_params_sends_minimal_body(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        model_cls: type,
        request: pytest.FixtureRequest,
    ) -> None:
        entity_data: dict[str, Any] = request.getfixturevalue(fixture_name)
        capture = RequestCapture(payload=entity_data)

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            await method(entity_data["id"])

        capture.assert_called_once()
        capture.last_request.assert_json_body({"fields": {}})
        assert "version" not in (capture.last_request.params or {})
