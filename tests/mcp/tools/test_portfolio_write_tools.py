from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import PortfolioEntity
from mcp_tracker.tracker.proto.types.inputs import EntityChecklistItemUpdateInput
from mcp_tracker.tracker.proto.types.issues import IssueComment
from tests.mcp.conftest import get_tool_result_content


class TestPortfolioCreate:
    async def test_creates_portfolio(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_create.return_value = sample_portfolio

        result = await client_session.call_tool(
            "portfolio_create", {"summary": "New Portfolio"}
        )

        assert not result.isError
        mock_entities_protocol.portfolio_create.assert_called_once_with(
            summary="New Portfolio",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
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
        assert content["id"] == sample_portfolio.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_create", {"summary": "New Portfolio"}
        )

        assert result.isError


class TestPortfolioUpdate:
    async def test_updates_portfolio(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_update.return_value = sample_portfolio

        result = await client_session.call_tool(
            "portfolio_update",
            {"entity_id": "def456", "entity_status": "cancelled"},
        )

        assert not result.isError
        mock_entities_protocol.portfolio_update.assert_called_once_with(
            "def456",
            summary=None,
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status="cancelled",
            parent_entity=None,
            team_access=None,
            comment=None,
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
            "portfolio_update", {"entity_id": "def456"}
        )

        assert result.isError


class TestPortfolioDelete:
    async def test_deletes_portfolio(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        mock_entities_protocol.portfolio_delete.return_value = None

        result = await client_session.call_tool(
            "portfolio_delete", {"entity_id": "def456"}
        )

        assert not result.isError
        mock_entities_protocol.portfolio_delete.assert_called_once_with(
            "def456", with_board=False, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_delete", {"entity_id": "def456"}
        )

        assert result.isError


class TestPortfolioAddComment:
    async def test_adds_comment(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comment: IssueComment,
    ) -> None:
        mock_entities_protocol.portfolio_add_comment.return_value = sample_comment

        result = await client_session.call_tool(
            "portfolio_add_comment",
            {"entity_id": "def456", "text": "Hello", "summonees": ["user123"]},
        )

        assert not result.isError
        mock_entities_protocol.portfolio_add_comment.assert_called_once_with(
            "def456",
            text="Hello",
            summonees=["user123"],
            maillist_summonees=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_comment.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_add_comment", {"entity_id": "def456", "text": "Hello"}
        )

        assert result.isError


class TestPortfolioUpdateComment:
    async def test_updates_comment(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comment: IssueComment,
    ) -> None:
        mock_entities_protocol.portfolio_update_comment.return_value = sample_comment

        result = await client_session.call_tool(
            "portfolio_update_comment",
            {"entity_id": "def456", "comment_id": 1, "text": "Updated"},
        )

        assert not result.isError
        mock_entities_protocol.portfolio_update_comment.assert_called_once_with(
            "def456",
            1,
            text="Updated",
            summonees=None,
            maillist_summonees=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_comment.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_update_comment",
            {"entity_id": "def456", "comment_id": 1, "text": "Updated"},
        )

        assert result.isError


class TestPortfolioDeleteComment:
    async def test_deletes_comment(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        mock_entities_protocol.portfolio_delete_comment.return_value = None

        result = await client_session.call_tool(
            "portfolio_delete_comment", {"entity_id": "def456", "comment_id": 1}
        )

        assert not result.isError
        mock_entities_protocol.portfolio_delete_comment.assert_called_once_with(
            "def456", 1, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_delete_comment", {"entity_id": "def456", "comment_id": 1}
        )

        assert result.isError


class TestPortfolioAddChecklistItem:
    async def test_adds_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_add_checklist_item.return_value = (
            sample_portfolio
        )

        result = await client_session.call_tool(
            "portfolio_add_checklist_item",
            {"entity_id": "def456", "text": "Do the thing", "checked": True},
        )

        assert not result.isError
        mock_entities_protocol.portfolio_add_checklist_item.assert_called_once_with(
            "def456",
            text="Do the thing",
            checked=True,
            assignee=None,
            deadline=None,
            fields=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_portfolio.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_add_checklist_item",
            {"entity_id": "def456", "text": "Do the thing"},
        )

        assert result.isError


class TestPortfolioUpdateChecklistItem:
    async def test_updates_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_update_checklist_item.return_value = (
            sample_portfolio
        )

        result = await client_session.call_tool(
            "portfolio_update_checklist_item",
            {"entity_id": "def456", "checklist_item_id": "item1", "checked": True},
        )

        assert not result.isError
        mock_entities_protocol.portfolio_update_checklist_item.assert_called_once_with(
            "def456",
            "item1",
            text=None,
            checked=True,
            assignee=None,
            deadline=None,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_update_checklist_item",
            {"entity_id": "def456", "checklist_item_id": "item1", "checked": True},
        )

        assert result.isError


class TestPortfolioMoveChecklistItem:
    async def test_moves_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_move_checklist_item.return_value = (
            sample_portfolio
        )

        result = await client_session.call_tool(
            "portfolio_move_checklist_item",
            {
                "entity_id": "def456",
                "checklist_item_id": "item1",
                "before": "item0",
            },
        )

        assert not result.isError
        mock_entities_protocol.portfolio_move_checklist_item.assert_called_once_with(
            "def456",
            "item1",
            before="item0",
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_move_checklist_item",
            {"entity_id": "def456", "checklist_item_id": "item1", "before": "item0"},
        )

        assert result.isError


class TestPortfolioDeleteChecklistItem:
    async def test_deletes_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_delete_checklist_item.return_value = (
            sample_portfolio
        )

        result = await client_session.call_tool(
            "portfolio_delete_checklist_item",
            {"entity_id": "def456", "checklist_item_id": "item1"},
        )

        assert not result.isError
        mock_entities_protocol.portfolio_delete_checklist_item.assert_called_once_with(
            "def456",
            "item1",
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_delete_checklist_item",
            {"entity_id": "def456", "checklist_item_id": "item1"},
        )

        assert result.isError


class TestPortfolioUpdateChecklist:
    async def test_updates_checklist(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_update_checklist.return_value = (
            sample_portfolio
        )

        result = await client_session.call_tool(
            "portfolio_update_checklist",
            {
                "entity_id": "def456",
                "items": [{"id": "item1", "text": "Do the thing", "checked": True}],
            },
        )

        assert not result.isError
        call_kwargs = mock_entities_protocol.portfolio_update_checklist.call_args.kwargs
        assert call_kwargs["items"] == [
            EntityChecklistItemUpdateInput(
                id="item1", text="Do the thing", checked=True
            )
        ]
        assert call_kwargs["fields"] is None

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_update_checklist",
            {
                "entity_id": "def456",
                "items": [{"id": "item1", "text": "Do the thing"}],
            },
        )

        assert result.isError


class TestPortfolioDeleteChecklist:
    async def test_deletes_checklist(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_delete_checklist.return_value = (
            sample_portfolio
        )

        result = await client_session.call_tool(
            "portfolio_delete_checklist", {"entity_id": "def456"}
        )

        assert not result.isError
        mock_entities_protocol.portfolio_delete_checklist.assert_called_once_with(
            "def456", fields=None, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "portfolio_delete_checklist", {"entity_id": "def456"}
        )

        assert result.isError
