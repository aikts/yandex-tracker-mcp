import datetime
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import BOARDS_PAGE_MAX, TrackerClient
from mcp_tracker.tracker.custom.errors import TrackerAPIError, TrackerAPITimeout
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import Board
from tests.aioresponses_utils import RequestCapture


class TestBoardsList:
    async def test_success(
        self, tracker_client: TrackerClient, sample_board_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=100",
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
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=100",
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
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=100",
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
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=100",
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
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=100",
                status=403,
                payload={"errorMessages": ["Нет доступа."], "statusCode": 403},
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.boards_list()

            assert exc_info.value.status == 403
            assert "Нет доступа." in str(exc_info.value)


class TestBoardsListTimeout:
    """A timeout has to say so.

    `str(TimeoutError())` is the empty string, so a timeout used to reach the
    caller as `Error executing tool boards_get_all:` with nothing after the
    colon - no hint that time, rather than the request, was the problem. It
    took a bad endpoint to expose that: `/v3/boards` returned the whole
    organization in 7-16s against a 10s budget. Paging removed the cause; the
    message stays, because no budget covers every organization.
    """

    async def test_a_timeout_says_so(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=100",
                exception=TimeoutError(),
            )

            with pytest.raises(TrackerAPITimeout) as exc_info:
                await tracker_client.boards_list()

        message = str(exc_info.value)
        assert message, "a timeout must not reach the caller as an empty message"
        assert "v3/boards" in message
        assert "TRACKER_API_TIMEOUT" in message


class TestBoardsListPaging:
    """`/v3/boards/_paginate` walks by board id, not by page number.

    It replaced `/v3/boards`, which ignored paging and answered with the whole
    organization - 1.4 MB and 7-16s for 415 boards, against a 10s default
    budget, in a different order every call. A page of 25 is 88 KB in 1-2s and
    comes back sorted by id.
    """

    async def test_per_page_is_sent(
        self, tracker_client: TrackerClient, sample_board_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=25",
                payload=[sample_board_data],
            )

            assert len(await tracker_client.boards_list(per_page=25)) == 1

    async def test_cursor_is_sent_as_the_id_to_start_after(
        self, tracker_client: TrackerClient, sample_board_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/_paginate?perPage=25&id=18",
                payload=[sample_board_data],
            )

            assert len(await tracker_client.boards_list(per_page=25, cursor=18)) == 1

    async def test_per_page_is_capped_at_the_documented_maximum(
        self, tracker_client: TrackerClient
    ) -> None:
        """The endpoint documents `perPage` as no more than 500."""
        with aioresponses() as m:
            m.get(
                f"https://api.tracker.yandex.net/v3/boards/_paginate?perPage={BOARDS_PAGE_MAX}",
                payload=[],
            )

            assert await tracker_client.boards_list(per_page=10_000) == []
