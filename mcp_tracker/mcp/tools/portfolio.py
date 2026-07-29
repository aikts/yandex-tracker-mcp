"""Portfolio-related MCP tools (read-only)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    EntityFieldsParam,
    EntityFilterParam,
    EntityID,
    EntityInputParam,
    EntityOrderAscParam,
    EntityOrderByParam,
    EntityRootOnlyParam,
    PageParam,
    PerPageParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import (
    PortfolioEntity,
    PortfolioSearchResult,
)


def register_portfolio_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register portfolio-related tools (all read-only)."""

    @mcp.tool(
        title="Get Portfolio",
        description="Get a Yandex Tracker portfolio by its id or shortId. "
        "A portfolio groups projects and/or other portfolios.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def portfolio_get(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        fields: EntityFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_get(
            entity_id,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Find Portfolios",
        description="Search Yandex Tracker portfolios by name substring and/or field filters.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def portfolio_find(
        ctx: Context[Any, AppContext],
        input: EntityInputParam = None,
        filter: EntityFilterParam = None,
        order_by: EntityOrderByParam = None,
        order_asc: EntityOrderAscParam = None,
        root_only: EntityRootOnlyParam = None,
        page: PageParam = 1,
        per_page: PerPageParam = 50,
        fields: EntityFieldsParam = None,
    ) -> PortfolioSearchResult:
        return await ctx.request_context.lifespan_context.entities.portfolio_find(
            input=input,
            filter=filter,
            order_by=order_by,
            order_asc=order_asc,
            root_only=root_only,
            per_page=per_page,
            page=page,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )
