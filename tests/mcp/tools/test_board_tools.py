from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.mcp.tools.board import BOARDS_SCAN_PAGE
from mcp_tracker.tracker.custom.errors import BoardNotFound
from mcp_tracker.tracker.proto.types.boards import Board, BoardColumnDetail, Sprint
from tests.mcp.conftest import get_tool_result_content
from tests.mcp.tools.conftest import make_board_on_queues


class TestBoardsGetAll:
    async def test_returns_boards(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_boards: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = sample_boards

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        mock_boards_protocol.boards_list.assert_called_once()
        content = get_tool_result_content(result)["boards"]
        assert isinstance(content, list)
        assert len(content) == len(sample_boards)
        assert content[0]["id"] == sample_boards[0].id
        assert content[0]["name"] == sample_boards[0].name
        assert [column["display"] for column in content[0]["columns"]] == [
            "Open",
            "In Progress",
        ]

    async def test_returns_empty_list(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.boards_list.return_value = []

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        assert get_tool_result_content(result)["boards"] == []

    async def test_pages_by_cursor(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """`/v3/boards/_paginate` walks by board id, so the tool passes it on."""
        mock_boards_protocol.boards_list.return_value = [
            Board.model_construct(id=i, name=f"Board {i}") for i in (2, 5)
        ]

        result = await client_session.call_tool(
            "boards_get_all", {"cursor": 18, "per_page": 2}
        )

        assert not result.isError
        assert mock_boards_protocol.boards_list.call_args.kwargs["cursor"] == 18
        assert mock_boards_protocol.boards_list.call_args.kwargs["per_page"] == 2

    async def test_a_full_page_offers_the_next_cursor(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """The cursor is the last board's id - the endpoint sorts by it."""
        mock_boards_protocol.boards_list.return_value = [
            Board.model_construct(id=i, name=f"Board {i}") for i in (2, 5, 8)
        ]

        result = await client_session.call_tool("boards_get_all", {"per_page": 3})

        assert not result.isError
        assert get_tool_result_content(result)["next_cursor"] == 8

    async def test_a_short_page_is_the_last_one(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.boards_list.return_value = [
            Board.model_construct(id=2, name="Board 2")
        ]

        result = await client_session.call_tool("boards_get_all", {"per_page": 3})

        assert not result.isError
        assert get_tool_result_content(result)["next_cursor"] is None

    async def test_an_empty_page_is_the_last_one(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.boards_list.return_value = []

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["boards"] == []
        assert content["next_cursor"] is None

    async def test_asks_for_a_bounded_page_by_default(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """An organization with hundreds of boards must not be dumped in one call."""
        mock_boards_protocol.boards_list.return_value = []

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        assert mock_boards_protocol.boards_list.call_args.kwargs["per_page"] == 25

    async def test_fields_trims_the_answer(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_boards: list[Board],
    ) -> None:
        """Searching for a board should not drag every board's settings along."""
        mock_boards_protocol.boards_list.return_value = sample_boards

        result = await client_session.call_tool(
            "boards_get_all", {"fields": ["id", "name"]}
        )

        assert not result.isError
        content = get_tool_result_content(result)["boards"]
        assert [sorted(board) for board in content] == [["id", "name"]] * len(
            sample_boards
        )

    async def test_without_fields_returns_everything(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_with_settings: Board,
    ) -> None:
        mock_boards_protocol.boards_list.return_value = [sample_board_with_settings]

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)["boards"]
        assert "autoFilterSettings" in content[0]
        assert content[0]["estimateBy"]["id"] == "storyPoints"

    async def test_queue_filters_by_the_boards_own_filter(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        """A board has no queue field - it is matched by the queue it collects."""
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        content = get_tool_result_content(result)["boards"]
        assert [board["id"] for board in content] == [1]

    async def test_queue_matches_a_board_collecting_several_queues(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool(
            "boards_get_all", {"queue": "SMARTBOTGOALS"}
        )

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)["boards"]] == [
            2
        ]

    async def test_queue_is_case_insensitive(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {"queue": "levelarm"})

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)["boards"]] == [
            1
        ]

    @pytest.mark.parametrize(
        ("field_id", "field_key"),
        [("queue", "queue"), ("queue", None), (None, "queue")],
    )
    async def test_queue_field_is_recognised_by_id_or_key(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        field_id: str | None,
        field_key: str | None,
    ) -> None:
        """A filter names the queue field twice; either spelling has to do."""
        mock_boards_protocol.boards_list.return_value = [
            make_board_on_queues(
                1, "Level ARM", "LEVELARM", field_id=field_id, field_key=field_key
            )
        ]

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)["boards"]] == [
            1
        ]

    async def test_inverted_condition_is_not_a_match(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        """ "queue is not LEVELARM" says which queue the board is *not* about."""
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        assert 3 not in [
            board["id"] for board in get_tool_result_content(result)["boards"]
        ]

    async def test_unknown_queue_returns_nothing(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {"queue": "NOSUCH"})

        assert not result.isError
        assert get_tool_result_content(result)["boards"] == []

    async def test_without_queue_returns_boards_naming_none(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        """Boards with no queue in their filter are only dropped when filtering."""
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        assert 4 in [board["id"] for board in get_tool_result_content(result)["boards"]]

    async def test_queue_sees_every_board_not_one_page_of_them(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """`per_page` counts matches, not boards read.

        A match can be anywhere, so filtering one page would answer "no boards"
        for a queue whose only board sits past the first 25 of an
        organization's 400-odd - which is why this branch reads the unpaged
        listing rather than walking `_paginate`.
        """
        boards = [make_board_on_queues(i, f"Board {i}", "OTHER") for i in range(60)]
        boards.append(make_board_on_queues(999, "The one", "LEVELARM"))
        mock_boards_protocol.boards_list.return_value = boards

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)["boards"]] == [
            999
        ]

    async def test_the_walk_advances_the_cursor_past_boards_it_examined(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """The cursor follows what was read, not what matched.

        Following the last *match* instead would rescan every board between two
        matches on the next call, and never terminate on a queue with none.
        """
        first = [make_board_on_queues(i, f"Board {i}", "OTHER") for i in range(1, 101)]
        second = [make_board_on_queues(150, "The one", "LEVELARM")]
        mock_boards_protocol.boards_list.side_effect = [first, second]

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)["boards"]] == [
            150
        ]
        # A full page is followed by a request starting after its last board,
        # and the short second page ends the walk.
        calls = mock_boards_protocol.boards_list.call_args_list
        assert calls[0].kwargs["cursor"] is None
        assert calls[1].kwargs["cursor"] == 100
        assert get_tool_result_content(result)["next_cursor"] is None

    async def test_the_walk_asks_for_a_page_at_a_time(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """Never one unbounded request.

        `/v3/boards` grows with the Tracker it is pointed at, so no timeout
        fits every organization; a page is bounded by `per_page` instead.
        """
        mock_boards_protocol.boards_list.return_value = []

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        assert (
            mock_boards_protocol.boards_list.call_args.kwargs["per_page"]
            == BOARDS_SCAN_PAGE
        )

    async def test_queue_combines_with_fields(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool(
            "boards_get_all", {"queue": "LEVELARM", "fields": ["id", "name"]}
        )

        assert not result.isError
        content = get_tool_result_content(result)["boards"]
        assert [sorted(board) for board in content] == [["id", "name"]]

    @pytest.mark.parametrize("queue", ["forbidden", "Forbidden", "FORBIDDEN"])
    async def test_restricted_queue_is_rejected(
        self,
        client_session_with_limits: ClientSession,
        mock_boards_protocol: AsyncMock,
        queue: str,
    ) -> None:
        """The match is case-insensitive, so the allow-list check has to be too.

        Checking the raw value while matching the upper-cased one let a
        lower-cased queue past the allow-list and answer for the queue it names.
        """
        mock_boards_protocol.boards_list.return_value = []

        result = await client_session_with_limits.call_tool(
            "boards_get_all", {"queue": queue}
        )

        assert result.isError
        mock_boards_protocol.boards_list.assert_not_called()

    @pytest.mark.parametrize("queue", ["allowed", "Allowed", "ALLOWED"])
    async def test_permitted_queue_is_allowed(
        self,
        client_session_with_limits: ClientSession,
        mock_boards_protocol: AsyncMock,
        queue: str,
    ) -> None:
        mock_boards_protocol.boards_list.return_value = [
            make_board_on_queues(1, "Allowed board", "ALLOWED")
        ]

        result = await client_session_with_limits.call_tool(
            "boards_get_all", {"queue": queue}
        )

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)["boards"]] == [
            1
        ]


class TestBoardGetSprints:
    async def test_returns_sprints(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprints: list[Sprint],
    ) -> None:
        mock_boards_protocol.board_get_sprints.return_value = sample_sprints

        result = await client_session.call_tool("board_get_sprints", {"board_id": 1})

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_sprints)
        assert [sprint["status"] for sprint in content] == [
            "released",
            "in_progress",
            "draft",
        ]

    async def test_passes_board_id(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprints: list[Sprint],
    ) -> None:
        mock_boards_protocol.board_get_sprints.return_value = sample_sprints

        result = await client_session.call_tool("board_get_sprints", {"board_id": 42})

        assert not result.isError
        mock_boards_protocol.board_get_sprints.assert_called_once()
        call_args = mock_boards_protocol.board_get_sprints.call_args
        assert call_args[0][0] == 42

    async def test_current_sprint_is_discoverable(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprints: list[Sprint],
        sample_sprint: Sprint,
    ) -> None:
        """The 'put an issue into the current sprint' scenario from the tool description."""
        mock_boards_protocol.board_get_sprints.return_value = sample_sprints

        result = await client_session.call_tool("board_get_sprints", {"board_id": 1})

        assert not result.isError
        content = get_tool_result_content(result)
        current = [sprint for sprint in content if sprint["status"] == "in_progress"]
        assert len(current) == 1
        assert current[0]["id"] == sample_sprint.id
        assert current[0]["startDate"] == "2015-06-01"
        assert current[0]["endDate"] == "2015-06-14"

    async def test_returns_empty_list(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.board_get_sprints.return_value = []

        result = await client_session.call_tool("board_get_sprints", {"board_id": 1})

        assert not result.isError
        assert get_tool_result_content(result) == []

    async def test_fields_trims_the_answer(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_sprints: list[Sprint],
    ) -> None:
        mock_boards_protocol.board_get_sprints.return_value = sample_sprints

        result = await client_session.call_tool(
            "board_get_sprints", {"board_id": 1, "fields": ["id", "name", "status"]}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert [sorted(sprint) for sprint in content] == [
            ["id", "name", "status"]
        ] * len(sample_sprints)


class TestBoardGet:
    async def test_returns_the_board_settings(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_with_settings: Board,
    ) -> None:
        mock_boards_protocol.board_get.return_value = sample_board_with_settings

        result = await client_session.call_tool("board_get", {"board_id": 1})

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["id"] == 1
        assert content["useRanking"] is False
        assert content["estimateBy"]["display"] == "Story Points"

    async def test_auto_filter_names_the_queue_the_board_collects(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_with_settings: Board,
    ) -> None:
        """The point of the tool: find out which issues land on a board."""
        mock_boards_protocol.board_get.return_value = sample_board_with_settings

        result = await client_session.call_tool("board_get", {"board_id": 1})

        assert not result.isError
        content = get_tool_result_content(result)
        fields = content["autoFilterSettings"]["addFilterSettings"]["liveFilter"][
            "fieldValues"
        ]
        assert [f["id"] for f in fields] == ["queue"]
        assert fields[0]["value"][0]["fixed"]["key"] == "LEVELARM"

    async def test_passes_board_id(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_with_settings: Board,
    ) -> None:
        mock_boards_protocol.board_get.return_value = sample_board_with_settings

        result = await client_session.call_tool("board_get", {"board_id": 42})

        assert not result.isError
        assert mock_boards_protocol.board_get.call_args[0][0] == 42

    async def test_fields_trims_the_answer(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_with_settings: Board,
    ) -> None:
        mock_boards_protocol.board_get.return_value = sample_board_with_settings

        result = await client_session.call_tool(
            "board_get", {"board_id": 1, "fields": ["id", "name"]}
        )

        assert not result.isError
        assert sorted(get_tool_result_content(result)) == ["id", "name"]


class TestBoardGetColumns:
    async def test_returns_columns_with_statuses(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_columns: list[BoardColumnDetail],
    ) -> None:
        mock_boards_protocol.board_get_columns.return_value = sample_board_columns

        result = await client_session.call_tool("board_get_columns", {"board_id": 1})

        assert not result.isError
        content = get_tool_result_content(result)
        assert [column["name"] for column in content] == ["Открыт", "В работе"]
        assert [s["key"] for s in content[0]["statuses"]] == ["open", "new"]
        assert [s["key"] for s in content[1]["statuses"]] == ["inProgress"]

    async def test_passes_board_id(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        sample_board_columns: list[BoardColumnDetail],
    ) -> None:
        mock_boards_protocol.board_get_columns.return_value = sample_board_columns

        result = await client_session.call_tool("board_get_columns", {"board_id": 42})

        assert not result.isError
        assert mock_boards_protocol.board_get_columns.call_args[0][0] == 42

    async def test_returns_empty_list(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.board_get_columns.return_value = []

        result = await client_session.call_tool("board_get_columns", {"board_id": 1})

        assert not result.isError
        assert get_tool_result_content(result) == []


class TestBoardNotFoundReachesTheCaller:
    """A 404 on a board-scoped path is only useful if the caller sees it.

    The client raises `BoardNotFound` on all three paths and that is covered
    there; what was not covered is that it comes out of the tool as an error
    rather than as an empty answer the agent then reasons from.
    """

    @pytest.mark.parametrize(
        ("tool_name", "protocol_method"),
        [
            ("board_get", "board_get"),
            ("board_get_columns", "board_get_columns"),
            ("board_get_sprints", "board_get_sprints"),
        ],
    )
    async def test_unknown_board_is_an_error(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        tool_name: str,
        protocol_method: str,
    ) -> None:
        getattr(mock_boards_protocol, protocol_method).side_effect = BoardNotFound(404)

        result = await client_session.call_tool(tool_name, {"board_id": 404})

        assert result.isError
