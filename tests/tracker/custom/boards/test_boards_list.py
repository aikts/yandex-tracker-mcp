import datetime
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import TrackerAPIError
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import Board
from tests.aioresponses_utils import RequestCapture


class TestBoardsList:
    async def test_success(
        self, tracker_client: TrackerClient, sample_board_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards",
                payload=[sample_board_data],
            )

            result = await tracker_client.boards_list()

            assert isinstance(result, list)
            assert len(result) == 1
            board = result[0]
            assert isinstance(board, Board)
            assert board.id == 1
            assert board.version == 1
            assert board.name == "My board"
            assert board.createdAt == datetime.datetime(
                2026, 1, 22, 9, 2, 18, 647000, tzinfo=datetime.timezone.utc
            )
            assert board.createdBy is not None
            assert board.createdBy.id == "username"
            assert board.columns is not None
            assert [column.display for column in board.columns] == [
                "Открыт",
                "В работе",
            ]

    async def test_multiple(
        self, tracker_client: TrackerClient, sample_board_data: dict[str, Any]
    ) -> None:
        second_board = {**sample_board_data, "id": 2, "name": "Another board"}

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards",
                payload=[sample_board_data, second_board],
            )

            result = await tracker_client.boards_list()

            assert len(result) == 2
            assert all(isinstance(board, Board) for board in result)
            assert [board.id for board in result] == [1, 2]
            assert [board.name for board in result] == ["My board", "Another board"]

    async def test_empty(self, tracker_client: TrackerClient) -> None:
        boards_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards",
                payload=boards_response,
            )

            result = await tracker_client.boards_list()

            assert result == []

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_board_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_board_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.boards_list(auth=yandex_auth_cloud)

            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_error_surfaces_the_api_explanation(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards",
                status=403,
                payload={"errorMessages": ["Нет доступа."], "statusCode": 403},
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.boards_list()

            assert exc_info.value.status == 403
            assert "Нет доступа." in str(exc_info.value)
