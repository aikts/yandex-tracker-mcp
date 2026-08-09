from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import (
    PortfolioEntity,
    PortfolioSearchResult,
)
from mcp_tracker.tracker.proto.types.issues import IssueComment
from tests.mcp.conftest import get_tool_result_content


class TestPortfolioGet:
    async def test_returns_portfolio(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_get.return_value = sample_portfolio

        result = await client_session.call_tool(
            "portfolio_get", {"entity_id": "def456"}
        )

        assert not result.isError
        mock_entities_protocol.portfolio_get.assert_called_once()
        content = get_tool_result_content(result)
        assert content["id"] == sample_portfolio.id
        assert sample_portfolio.fields is not None
        assert content["fields"]["summary"] == sample_portfolio.fields.summary

    async def test_passes_entity_id_and_fields(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_get.return_value = sample_portfolio

        await client_session.call_tool(
            "portfolio_get",
            {"entity_id": "def456", "fields": ["summary", "entityStatus"]},
        )

        mock_entities_protocol.portfolio_get.assert_called_once_with(
            "def456", fields=["summary", "entityStatus"], auth=YandexAuth()
        )

    async def test_omitted_fields_passed_as_none(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolio: PortfolioEntity,
    ) -> None:
        mock_entities_protocol.portfolio_get.return_value = sample_portfolio

        await client_session.call_tool("portfolio_get", {"entity_id": "def456"})

        call_kwargs = mock_entities_protocol.portfolio_get.call_args.kwargs
        assert call_kwargs["fields"] is None


class TestPortfolioFind:
    async def test_returns_portfolios(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolios: PortfolioSearchResult,
    ) -> None:
        mock_entities_protocol.portfolio_find.return_value = sample_portfolios

        result = await client_session.call_tool("portfolio_find", {})

        assert not result.isError
        mock_entities_protocol.portfolio_find.assert_called_once()
        content = get_tool_result_content(result)
        assert content["hits"] == sample_portfolios.hits
        assert len(content["values"]) == len(sample_portfolios.values)

    async def test_passes_search_parameters(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolios: PortfolioSearchResult,
    ) -> None:
        mock_entities_protocol.portfolio_find.return_value = sample_portfolios

        await client_session.call_tool(
            "portfolio_find",
            {
                "input": "test",
                "filter": {"entityStatus": "in_progress"},
                "order_by": "summary",
                "order_asc": False,
                "root_only": True,
                "page": 3,
                "per_page": 10,
            },
        )

        mock_entities_protocol.portfolio_find.assert_called_once_with(
            input="test",
            filter={"entityStatus": "in_progress"},
            order_by="summary",
            order_asc=False,
            root_only=True,
            per_page=10,
            page=3,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_optional_parameters_omitted(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_portfolios: PortfolioSearchResult,
    ) -> None:
        mock_entities_protocol.portfolio_find.return_value = sample_portfolios

        await client_session.call_tool("portfolio_find", {})

        call_kwargs = mock_entities_protocol.portfolio_find.call_args.kwargs
        assert call_kwargs["input"] is None
        assert call_kwargs["filter"] is None
        assert call_kwargs["order_by"] is None
        assert call_kwargs["order_asc"] is None
        assert call_kwargs["root_only"] is None


class TestPortfolioGetComments:
    async def test_returns_comments(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_entities_protocol.portfolio_get_comments.return_value = sample_comments

        result = await client_session.call_tool(
            "portfolio_get_comments", {"entity_id": "def456"}
        )

        assert not result.isError
        mock_entities_protocol.portfolio_get_comments.assert_called_once_with(
            "def456", auth=YandexAuth()
        )
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_comments)
        assert content[0]["text"] == sample_comments[0].text
