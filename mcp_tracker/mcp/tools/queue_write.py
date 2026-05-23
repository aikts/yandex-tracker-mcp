"""Queue write MCP tools (conditionally registered based on read-only mode)."""

import datetime
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import QueueID
from mcp_tracker.mcp.tools._access import check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.queues import QueueVersion


def register_queue_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register queue write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Queue Version",
        description="Create a new version in a Yandex Tracker queue.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def queue_create_version(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        name: Annotated[str, Field(description="Version name")],
        description: Annotated[
            str | None,
            Field(description="Optional version description"),
        ] = None,
        start_date: Annotated[
            datetime.date | None,
            Field(description="Optional version start date in YYYY-MM-DD format"),
        ] = None,
        due_date: Annotated[
            datetime.date | None,
            Field(description="Optional version due date in YYYY-MM-DD format"),
        ] = None,
    ) -> QueueVersion:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.queues.queue_create_version(
            queue_id,
            name=name,
            description=description,
            start_date=start_date,
            due_date=due_date,
            auth=get_yandex_auth(ctx),
        )
