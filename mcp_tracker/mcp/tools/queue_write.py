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
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion


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

    @mcp.tool(
        title="Create Queue",
        description=(
            "Create a Yandex Tracker queue. Requires key, name, lead and an "
            "issue_types_config with a valid workflow id (org-specific). Commonly used "
            "to make a throwaway queue for bulk-deleting issues: create it, move issues "
            "in (issue_move), then delete the queue (queue_delete)."
        ),
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def queue_create(
        ctx: Context[Any, AppContext],
        key: Annotated[
            str, Field(description="Queue key (uppercase latin), e.g. 'TRASH'")
        ],
        name: Annotated[str, Field(description="Queue name")],
        lead: Annotated[str, Field(description="Queue owner login or uid")],
        default_type: Annotated[
            str, Field(description="Default issue type key/id")
        ] = "task",
        default_priority: Annotated[
            str, Field(description="Default priority key/id")
        ] = "normal",
        issue_types_config: Annotated[
            list[dict[str, Any]] | None,
            Field(
                description='Issue type settings, e.g. [{"issueType": "task", '
                '"workflow": "<workflowId>", "resolutions": ["wontFix"]}]. '
                "workflow is required and org-specific."
            ),
        ] = None,
    ) -> Queue:
        return await ctx.request_context.lifespan_context.queues.queue_create(
            key=key,
            name=name,
            lead=lead,
            default_type=default_type,
            default_priority=default_priority,
            issue_types_config=issue_types_config,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Queue",
        description=(
            "Delete a Yandex Tracker queue together with ALL its issues. This is the "
            "only way to delete issues (Tracker has no per-issue delete — DELETE on an "
            "issue returns 405). Deletion is deferred: the queue is marked deleted and "
            "restorable via API for a while. Destructive."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def queue_delete(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> None:
        check_queue_access(settings, queue_id)
        await ctx.request_context.lifespan_context.queues.queue_delete(
            queue_id,
            auth=get_yandex_auth(ctx),
        )
