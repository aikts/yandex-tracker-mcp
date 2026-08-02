from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import GoalEntity
from tests.mcp.conftest import get_tool_result_content


class TestGoalCreate:
    async def test_creates_goal(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goal: GoalEntity,
    ) -> None:
        mock_entities_protocol.goal_create.return_value = sample_goal

        result = await client_session.call_tool("goal_create", {"summary": "New Goal"})

        assert not result.isError
        mock_entities_protocol.goal_create.assert_called_once_with(
            summary="New Goal",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            links=None,
            fields=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_goal.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "goal_create", {"summary": "New Goal"}
        )

        assert result.isError


class TestGoalUpdate:
    async def test_updates_goal(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goal: GoalEntity,
    ) -> None:
        mock_entities_protocol.goal_update.return_value = sample_goal

        result = await client_session.call_tool(
            "goal_update",
            {"entity_id": "ghi789", "entity_status": "achieved", "comment": "done"},
        )

        assert not result.isError
        mock_entities_protocol.goal_update.assert_called_once_with(
            "ghi789",
            summary=None,
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            end=None,
            tags=None,
            entity_status="achieved",
            parent_entity=None,
            team_access=None,
            comment="done",
            version=None,
            links=None,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "goal_update", {"entity_id": "ghi789"}
        )

        assert result.isError


class TestGoalDelete:
    async def test_deletes_goal(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        mock_entities_protocol.goal_delete.return_value = None

        result = await client_session.call_tool("goal_delete", {"entity_id": "ghi789"})

        assert not result.isError
        mock_entities_protocol.goal_delete.assert_called_once_with(
            "ghi789", with_board=False, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "goal_delete", {"entity_id": "ghi789"}
        )

        assert result.isError
