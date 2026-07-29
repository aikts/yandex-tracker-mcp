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

ENTITY_CREATE_CASES = [
    ("project", "project_create", "sample_project_data", ProjectEntity),
    ("portfolio", "portfolio_create", "sample_portfolio_data", PortfolioEntity),
    ("goal", "goal_create", "sample_goal_data", GoalEntity),
]


class TestEntityCreate:
    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_CREATE_CASES
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
        capture = RequestCapture(status=201, payload=entity_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            result = await method(summary="Test Summary")

            assert isinstance(result, model_cls)
            assert result.id == entity_data["id"]  # type: ignore[attr-defined]

        capture.assert_called_once()
        capture.last_request.assert_json_body({"fields": {"summary": "Test Summary"}})

    async def test_project_create_passes_full_fields(
        self,
        tracker_client: TrackerClient,
        sample_project_data: dict[str, Any],
    ) -> None:
        capture = RequestCapture(status=201, payload=sample_project_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    r"^https://api\.tracker\.yandex\.net/v3/entities/project(\?.*)?$"
                ),
                callback=capture.callback,
            )

            await tracker_client.project_create(
                summary="Q1 Launch",
                description="Launch project",
                lead="j.doe",
                team_users=["a.ivanov"],
                clients=["c.petrov"],
                followers=["f.sidorov"],
                tags=["urgent"],
                entity_status="in_progress",
                team_access=True,
            )

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "fields": {
                    "summary": "Q1 Launch",
                    "description": "Launch project",
                    "lead": "j.doe",
                    "teamUsers": ["a.ivanov"],
                    "clients": ["c.petrov"],
                    "followers": ["f.sidorov"],
                    "tags": ["urgent"],
                    "entityStatus": "in_progress",
                    "teamAccess": True,
                }
            }
        )
