import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.entities import (
    DEFAULT_ENTITY_FIELDS_PARAM,
    GoalEntity,
    PortfolioEntity,
    ProjectEntity,
)
from tests.aioresponses_utils import RequestCapture

ENTITY_GET_CASES = [
    ("project", "project_get", "sample_project_data", ProjectEntity),
    ("portfolio", "portfolio_get", "sample_portfolio_data", PortfolioEntity),
    ("goal", "goal_get", "sample_goal_data", GoalEntity),
]


class TestEntityGet:
    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_GET_CASES
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
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            result = await method(entity_data["id"])

            assert isinstance(result, model_cls)
            assert result.id == entity_data["id"]  # type: ignore[attr-defined]
            assert result.shortId == entity_data["shortId"]  # type: ignore[attr-defined]
            assert result.entityType == entity_type  # type: ignore[attr-defined]
            assert result.fields is not None  # type: ignore[attr-defined]
            assert result.fields.summary == entity_data["fields"]["summary"]  # type: ignore[attr-defined]
            assert (
                result.fields.entityStatus  # type: ignore[attr-defined]
                == entity_data["fields"]["entityStatus"]
            )

        capture.assert_called_once()
        capture.last_request.assert_params(
            {"fields": DEFAULT_ENTITY_FIELDS_PARAM[entity_type]}
        )

    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_GET_CASES
    )
    async def test_with_explicit_fields(
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
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            result = await method(entity_data["id"], fields=["summary"])

            assert isinstance(result, model_cls)

        capture.assert_called_once()
        capture.last_request.assert_params({"fields": "summary"})
