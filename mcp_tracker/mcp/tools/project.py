"""Project-related MCP tools (read-only)."""

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
from mcp_tracker.tracker.proto.types.entities import ProjectEntity, ProjectSearchResult


def register_project_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register project-related tools (all read-only)."""

    @mcp.tool(
        title="Get Project",
        description="Get a Yandex Tracker project by its id or shortId. "
        "A project groups issues and is distinct from a queue.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def project_get(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        fields: EntityFieldsParam = None,
    ) -> ProjectEntity:
        return await ctx.request_context.lifespan_context.entities.project_get(
            entity_id,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Find Projects",
        description="Search Yandex Tracker projects by name substring and/or field filters.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def project_find(
        ctx: Context[Any, AppContext],
        input: EntityInputParam = None,
        filter: EntityFilterParam = None,
        order_by: EntityOrderByParam = None,
        order_asc: EntityOrderAscParam = None,
        root_only: EntityRootOnlyParam = None,
        page: PageParam = 1,
        per_page: PerPageParam = 50,
        fields: EntityFieldsParam = None,
    ) -> ProjectSearchResult:
        return await ctx.request_context.lifespan_context.entities.project_find(
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
