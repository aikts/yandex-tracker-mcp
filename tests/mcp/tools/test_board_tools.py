from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

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
        content = get_tool_result_content(result)
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
        assert get_tool_result_content(result) == []

    @pytest.mark.parametrize(
        ("page", "per_page", "expected_ids"),
        [
            (1, 2, [0, 1]),
            (2, 2, [2, 3]),
            (3, 2, [4]),
            (4, 2, []),
            (1, 10, [0, 1, 2, 3, 4]),
        ],
    )
    async def test_pages_the_listing(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        page: int,
        per_page: int,
        expected_ids: list[int],
    ) -> None:
        """`GET /v3/boards` returns every board at once, so the tool pages it itself."""
        mock_boards_protocol.boards_list.return_value = [
            Board.model_construct(id=i, name=f"Board {i}") for i in range(5)
        ]

        result = await client_session.call_tool(
            "boards_get_all", {"page": page, "per_page": per_page}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert [board["id"] for board in content] == expected_ids

    async def test_defaults_to_the_first_page(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """An organization with hundreds of boards must not be dumped in one call."""
        mock_boards_protocol.boards_list.return_value = [
            Board.model_construct(id=i, name=f"Board {i}") for i in range(404)
        ]

        result = await client_session.call_tool("boards_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content) == 50
        assert content[0]["id"] == 0

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
        content = get_tool_result_content(result)
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
        content = get_tool_result_content(result)
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
        content = get_tool_result_content(result)
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
        assert [board["id"] for board in get_tool_result_content(result)] == [2]

    async def test_queue_is_case_insensitive(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {"queue": "levelarm"})

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)] == [1]

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
        assert 3 not in [board["id"] for board in get_tool_result_content(result)]

    async def test_unknown_queue_returns_nothing(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
        boards_across_queues: list[Board],
    ) -> None:
        mock_boards_protocol.boards_list.return_value = boards_across_queues

        result = await client_session.call_tool("boards_get_all", {"queue": "NOSUCH"})

        assert not result.isError
        assert get_tool_result_content(result) == []

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
        assert 4 in [board["id"] for board in get_tool_result_content(result)]

    async def test_queue_filter_runs_before_paging(
        self,
        client_session: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """Paging the unfiltered list first would make page 1 come back near-empty."""
        boards = [make_board_on_queues(i, f"Board {i}", "OTHER") for i in range(60)]
        boards.append(make_board_on_queues(999, "The one", "LEVELARM"))
        mock_boards_protocol.boards_list.return_value = boards

        result = await client_session.call_tool("boards_get_all", {"queue": "LEVELARM"})

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)] == [999]

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
        content = get_tool_result_content(result)
        assert [sorted(board) for board in content] == [["id", "name"]]

    async def test_restricted_queue_is_rejected(
        self,
        client_session_with_limits: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        """Scoping to a queue outside TRACKER_LIMIT_QUEUES must not answer."""
        mock_boards_protocol.boards_list.return_value = []

        result = await client_session_with_limits.call_tool(
            "boards_get_all", {"queue": "FORBIDDEN"}
        )

        assert result.isError
        mock_boards_protocol.boards_list.assert_not_called()

    async def test_permitted_queue_is_allowed(
        self,
        client_session_with_limits: ClientSession,
        mock_boards_protocol: AsyncMock,
    ) -> None:
        mock_boards_protocol.boards_list.return_value = [
            make_board_on_queues(1, "Allowed board", "ALLOWED")
        ]

        result = await client_session_with_limits.call_tool(
            "boards_get_all", {"queue": "ALLOWED"}
        )

        assert not result.isError
        assert [board["id"] for board in get_tool_result_content(result)] == [1]


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
