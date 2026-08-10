from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.boards import Board, Sprint
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
