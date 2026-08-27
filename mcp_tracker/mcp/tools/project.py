"""Project-related MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    CommentsCursorParam,
    CursorPerPageParam,
    EntityFilterParam,
    EntityID,
    EntityInputParam,
    EntityOrderAscParam,
    EntityOrderByParam,
    EntityRootOnlyParam,
    PageParam,
    PerPageParam,
    ProjectFieldsParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import (
    ProjectEntity,
    ProjectSearchResult,
)
from mcp_tracker.tracker.proto.types.issues import CommentFieldsEnum, CommentsPage


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
        fields: ProjectFieldsParam = None,
    ) -> ProjectEntity:
        return await ctx.request_context.lifespan_context.entities.project_get(
            entity_id,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Find Projects",
        description="Search Yandex Tracker projects by name substring and/or field filters. Paginated.",
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
        fields: ProjectFieldsParam = None,
    ) -> ProjectSearchResult:
        return await ctx.request_context.lifespan_context.entities.project_find(
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
        title="Get Project Comments",
        description="Get a page of comments of a Yandex Tracker project by its id or "
        "shortId, e.g. 'abc123'. Returns the comments plus `next_cursor` - pass it "
        "back as `cursor` until it is null.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def project_get_comments(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        per_page: CursorPerPageParam = 50,
        cursor: CommentsCursorParam = None,
        fields: Annotated[
            list[CommentFieldsEnum] | None,
            Field(
                description="Fields to include in each comment; omit to get all. "
                "text/text_html can be large, so select only what you need.",
            ),
        ] = None,
    ) -> CommentsPage:
        page = await ctx.request_context.lifespan_context.entities.project_get_comments(
            entity_id,
            per_page=per_page,
            cursor=cursor,
            auth=get_yandex_auth(ctx),
        )

        if fields is not None:
            set_non_needed_fields_null(page.comments, {f.name for f in fields})

        return page
