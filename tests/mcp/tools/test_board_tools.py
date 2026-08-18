from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.boards import Board, BoardColumnDetail, Sprint
from tests.mcp.conftest import get_tool_result_content


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
