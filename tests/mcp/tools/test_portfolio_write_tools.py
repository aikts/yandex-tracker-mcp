from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import PortfolioEntity
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
