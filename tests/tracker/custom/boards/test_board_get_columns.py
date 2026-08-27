from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import BoardNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import BoardColumnDetail
from tests.aioresponses_utils import RequestCapture


class TestBoardGetColumns:
    async def test_success(
        self,
        tracker_client: TrackerClient,
        sample_board_columns_data: list[dict[str, Any]],
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1/columns",
                payload=sample_board_columns_data,
            )

            columns = await tracker_client.board_get_columns(1)

            assert len(columns) == 2
            assert all(isinstance(c, BoardColumnDetail) for c in columns)
            assert [c.id for c in columns] == [1, 2]
            assert [c.name for c in columns] == ["Открыт", "В работе"]

    async def test_maps_statuses_onto_columns(
        self,
        tracker_client: TrackerClient,
        sample_board_columns_data: list[dict[str, Any]],
    ) -> None:
        """The statuses are the point of this endpoint - nested columns have none."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1/columns",
                payload=sample_board_columns_data,
            )

            columns = await tracker_client.board_get_columns(1)

            assert columns[0].statuses is not None
            assert [s.key for s in columns[0].statuses] == ["open", "new"]
            assert columns[0].statuses[0].display == "Открыт"
            assert columns[1].statuses is not None
            assert [s.key for s in columns[1].statuses] == ["inProgress"]

    async def test_empty(self, tracker_client: TrackerClient) -> None:
        columns_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/9/columns",
                payload=columns_response,
            )

            assert await tracker_client.board_get_columns(9) == []

    async def test_missing_board_raises_board_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/99999999/columns",
                status=404,
                payload={"errorMessages": ["Доска не существует."], "statusCode": 404},
            )

            with pytest.raises(BoardNotFound) as exc_info:
                await tracker_client.board_get_columns(99999999)

            assert exc_info.value.board_id == 99999999

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_board_columns_data: list[dict[str, Any]],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_board_columns_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1/columns",
                callback=capture.callback,
            )

            columns = await tracker_client_no_org.board_get_columns(
                1, auth=yandex_auth_cloud
            )

            assert len(columns) == 2

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
