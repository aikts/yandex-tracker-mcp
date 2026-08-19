import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.entities import (
    DEFAULT_ENTITY_FIELDS_PARAM,
    GoalSearchResult,
    PortfolioSearchResult,
    ProjectSearchResult,
)
from tests.aioresponses_utils import RequestCapture

ENTITY_SEARCH_CASES = [
    ("project", "project_find", "sample_project_search_data", ProjectSearchResult),
    (
        "portfolio",
        "portfolio_find",
        "sample_portfolio_search_data",
        PortfolioSearchResult,
    ),
    ("goal", "goal_find", "sample_goal_search_data", GoalSearchResult),
]


class TestEntitySearch:
    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_SEARCH_CASES
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
        search_data: dict[str, Any] = request.getfixturevalue(fixture_name)
        capture = RequestCapture(payload=search_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/_search(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            result = await method()

            assert isinstance(result, model_cls)
            assert result.hits == search_data["hits"]  # type: ignore[attr-defined]
            assert result.pages == search_data["pages"]  # type: ignore[attr-defined]
            assert len(result.values) == len(search_data["values"])  # type: ignore[attr-defined]

        capture.assert_called_once()
        capture.last_request.assert_params(
            {
                "page": 1,
                "perPage": 50,
                "fields": DEFAULT_ENTITY_FIELDS_PARAM[entity_type],
            }
        )

    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_SEARCH_CASES
    )
    async def test_passes_search_parameters(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        model_cls: type,
        request: pytest.FixtureRequest,
    ) -> None:
        search_data: dict[str, Any] = request.getfixturevalue(fixture_name)
        capture = RequestCapture(payload=search_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/_search(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            await method(
                input="test",
                filter={"entityStatus": "in_progress"},
                order_by="summary",
                order_asc=True,
                root_only=True,
                per_page=25,
                page=2,
            )

        capture.assert_called_once()
        capture.last_request.assert_params({"page": 2, "perPage": 25})
        capture.last_request.assert_json_body(
            {
                "input": "test",
                "filter": {"entityStatus": "in_progress"},
                "orderBy": "summary",
                "orderAsc": True,
                "rootOnly": True,
            }
        )

    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name,model_cls", ENTITY_SEARCH_CASES
    )
    async def test_optional_parameters_omitted_from_body(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        model_cls: type,
        request: pytest.FixtureRequest,
    ) -> None:
        search_data: dict[str, Any] = request.getfixturevalue(fixture_name)
        capture = RequestCapture(payload=search_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/_search(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            await method()

        capture.assert_called_once()
        capture.last_request.assert_json_body({})
