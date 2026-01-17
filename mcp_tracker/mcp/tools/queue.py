"""Queue-related MCP tools (read-only)."""

import asyncio
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PerPageParam, QueueID
from mcp_tracker.mcp.tools._access import check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.queues import (
    Queue,
    QueueExpandOption,
    QueueFieldsEnum,
    QueueVersion,
)


def register_queue_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register queue-related tools (all read-only)."""

    @mcp.tool(
        title="Get All Queues",
        description="Find all Yandex Tracker queues available to the user (queue is a project in some sense)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queues_get_all(
        ctx: Context[Any, AppContext, Request],
        fields: Annotated[
            list[QueueFieldsEnum] | None,
            Field(
                description="Fields to include in the response. In order to not pollute context window - "
                "select appropriate fields beforehand. Not specifying fields will return all available. "
                "Most of the time one needs key and name only.",
            ),
        ] = None,
        page: Annotated[
            int | None,
            Field(
                description="Page number to return, default is None which means to retrieve all pages. "
                "Specify page number to retrieve a specific page when context limit is reached.",
            ),
        ] = None,
        per_page: PerPageParam = 100,
    ) -> list[Queue]:
        result: list[Queue] = []

        fetch_all_pages = page is None
        if fetch_all_pages:
            page = 1

        # At this point page is always an int
        assert page is not None

        while True:
            queues = await ctx.request_context.lifespan_context.queues.queues_list(
                per_page=per_page,
                page=page,
                auth=get_yandex_auth(ctx),
            )
            if len(queues) == 0:
                break

            if settings.tracker_limit_queues:
                queues = [
                    queue
                    for queue in queues
                    if queue.key in set(settings.tracker_limit_queues)
                ]

            result.extend(queues)

            if not fetch_all_pages:
                break  # Only fetch the requested page
            page += 1

        if fields is not None:
            set_non_needed_fields_null(result, {f.name for f in fields})

        return result

    @mcp.tool(
        title="Get Queue Tags",
        description="Get all tags for a specific Yandex Tracker queue",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_tags(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[str]:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.queues.queues_get_tags(
            queue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Queue Versions",
        description="Get all versions for a specific Yandex Tracker queue",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_versions(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[QueueVersion]:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.queues.queues_get_versions(
            queue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Queue Fields",
        description="Get fields for a specific Yandex Tracker queue. "
        "Returns list of global fields and optionally local (queue-specific) fields. "
        "The schema.required property indicates whether a field is mandatory. "
        "Use this to find available and required fields before creating an issue with issue_create tool.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_fields(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        include_local_fields: Annotated[
            bool,
            Field(
                description="Whether to include queue-specific local fields in the response. "
                "When True, makes parallel requests to get both global and local fields."
            ),
        ] = True,
    ) -> list[GlobalField]:
        check_queue_access(settings, queue_id)

        auth = get_yandex_auth(ctx)
        queues = ctx.request_context.lifespan_context.queues

        if not include_local_fields:
            return await queues.queues_get_fields(queue_id, auth=auth)

        async with asyncio.TaskGroup() as tg:
            global_fields_task = tg.create_task(
                queues.queues_get_fields(queue_id, auth=auth)
            )
            local_fields_task = tg.create_task(
                queues.queues_get_local_fields(queue_id, auth=auth)
            )
        return global_fields_task.result() + local_fields_task.result()

    @mcp.tool(
        title="Get Queue Metadata",
        description="Get detailed metadata about a specific Yandex Tracker queue. "
        "Returns queue information including name, description, default type/priority, "
        "and optionally expanded data like issue types with their resolutions, workflows, team members, etc. "
        "Use expand=['issueTypesConfig'] to get available resolutions for issue_close tool.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_metadata(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        expand: Annotated[
            list[QueueExpandOption] | None,
            Field(
                description="Optional list of fields to expand in the response. "
                "Available options: 'all', 'projects', 'components', 'versions', 'types', "
                "'team', 'workflows', 'fields', 'issueTypesConfig'. "
                "Use 'issueTypesConfig' to get available resolutions for each issue type."
            ),
        ] = None,
    ) -> Queue:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.queues.queue_get(
            queue_id,
            expand=expand,
            auth=get_yandex_auth(ctx),
        )
