"""Goal-related MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    EntityID,
    EntityInputParam,
    EntityOrderAscParam,
    EntityOrderByParam,
    EntityRootOnlyParam,
    GoalFilterParam,
    PageParam,
    PerPageParam,
    entity_fields_description,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import (
    DEFAULT_ENTITY_FIELDS,
    GoalEntity,
    GoalFieldsEnum,
    GoalSearchResult,
)

GoalFieldsParam = Annotated[
    list[GoalFieldsEnum] | None,
    Field(description=entity_fields_description(DEFAULT_ENTITY_FIELDS)),
]


def register_goal_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register goal-related tools (all read-only)."""

    @mcp.tool(
        title="Get Goal",
        description="Get a Yandex Tracker goal by its id or shortId.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def goal_get(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        fields: GoalFieldsParam = None,
    ) -> GoalEntity:
        return await ctx.request_context.lifespan_context.entities.goal_get(
            entity_id,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Find Goals",
        description="Search Yandex Tracker goals by name substring and/or field filters. Paginated: "
        "call again with `page` incremented (starting from 1) until an empty result is returned "
        "to retrieve all matches.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def goal_find(
        ctx: Context[Any, AppContext],
        input: EntityInputParam = None,
        filter: GoalFilterParam = None,
        order_by: EntityOrderByParam = None,
        order_asc: EntityOrderAscParam = None,
        root_only: EntityRootOnlyParam = None,
        page: PageParam = 1,
        per_page: PerPageParam = 50,
        fields: GoalFieldsParam = None,
    ) -> GoalSearchResult:
        return await ctx.request_context.lifespan_context.entities.goal_find(
            input=input,
            filter=filter,
            order_by=order_by,
            order_asc=order_asc,
            root_only=root_only,
            per_page=per_page,
            page=page,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )
