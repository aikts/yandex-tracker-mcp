"""Goal-related MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    CommentsCursorParam,
    CursorPerPageParam,
    EntityID,
    EntityInputParam,
    EntityOrderAscParam,
    EntityOrderByParam,
    EntityRootOnlyParam,
    GoalFieldsParam,
    GoalFilterParam,
    PageParam,
    PerPageParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import (
    GoalEntity,
    GoalSearchResult,
)
from mcp_tracker.tracker.proto.types.issues import CommentFieldsEnum, CommentsPage


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
        description="Search Yandex Tracker goals by name substring and/or field filters. Paginated.",
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

    @mcp.tool(
        title="Get Goal Comments",
        description="Get a page of comments of a Yandex Tracker goal by its id or shortId, "
        "e.g. 'ghi789'. Returns the comments plus 'next_cursor'. To fetch the next "
        "page, pass 'next_cursor' from the previous result as the 'cursor' argument; when "
        "'next_cursor' is null there are no more comments.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def goal_get_comments(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        per_page: CursorPerPageParam = 50,
        cursor: CommentsCursorParam = None,
        fields: Annotated[
            list[CommentFieldsEnum] | None,
            Field(
                description="Fields to include in each comment. In order to not pollute the context "
                "window - select only the fields you need (comment text/text_html can be large). "
                "Not specifying this returns all available fields.",
            ),
        ] = None,
    ) -> CommentsPage:
        page = await ctx.request_context.lifespan_context.entities.goal_get_comments(
            entity_id,
            per_page=per_page,
            cursor=cursor,
            auth=get_yandex_auth(ctx),
        )

        if fields is not None:
            set_non_needed_fields_null(page.comments, {f.name for f in fields})

        return page
