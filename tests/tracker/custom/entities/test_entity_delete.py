import re

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from tests.aioresponses_utils import RequestCapture

ENTITY_DELETE_CASES = [
    ("project", "project_delete", "sample_project_data"),
    ("portfolio", "portfolio_delete", "sample_portfolio_data"),
    ("goal", "goal_delete", "sample_goal_data"),
]


class TestEntityDelete:
    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name", ENTITY_DELETE_CASES
    )
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        request: pytest.FixtureRequest,
    ) -> None:
        entity_data = request.getfixturevalue(fixture_name)
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            result = await method(entity_data["id"])

            assert result is None

        capture.assert_called_once()
        assert "withBoard" not in (capture.last_request.params or {})

    @pytest.mark.parametrize(
        "entity_type,method_name,fixture_name", ENTITY_DELETE_CASES
    )
    async def test_with_board(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        method_name: str,
        fixture_name: str,
        request: pytest.FixtureRequest,
    ) -> None:
        entity_data = request.getfixturevalue(fixture_name)
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_data['id']}(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, method_name)
            await method(entity_data["id"], with_board=True)

        capture.assert_called_once()
        capture.last_request.assert_params({"withBoard": "true"})
