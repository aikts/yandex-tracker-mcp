"""Global field and metadata MCP tools (read-only)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueID
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status


def register_field_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register global field and metadata tools (all read-only)."""

    @mcp.tool(
        title="Get Global Fields",
        description="Get all global fields available in Yandex Tracker that can be used in issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_global_fields(
        ctx: Context[Any, AppContext],
    ) -> list[GlobalField]:
        return await ctx.request_context.lifespan_context.fields.get_global_fields(
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Statuses",
        description="Get all statuses available in Yandex Tracker that can be used in issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_statuses(
        ctx: Context[Any, AppContext],
    ) -> list[Status]:
        return await ctx.request_context.lifespan_context.fields.get_statuses(
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Issue Types",
        description="Get all issue types available in Yandex Tracker that can be used when creating or updating issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_issue_types(
        ctx: Context[Any, AppContext],
    ) -> list[IssueType]:
        return await ctx.request_context.lifespan_context.fields.get_issue_types(
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Priorities",
        description="Get all priorities available in Yandex Tracker that can be used in issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_priorities(
        ctx: Context[Any, AppContext],
    ) -> list[Priority]:
        return await ctx.request_context.lifespan_context.fields.get_priorities(
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Resolutions",
        description="Get all resolutions available in Yandex Tracker that can be used when closing issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_resolutions(
        ctx: Context[Any, AppContext],
    ) -> list[Resolution]:
        return await ctx.request_context.lifespan_context.fields.get_resolutions(
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Issue URL",
        description="Get a Yandex Tracker issue url by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_url(
        issue_id: IssueID,
    ) -> str:
        return f"https://tracker.yandex.ru/{issue_id}"
