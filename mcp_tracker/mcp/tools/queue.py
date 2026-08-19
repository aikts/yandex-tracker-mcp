"""Queue-related MCP tools (read-only)."""

import asyncio
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageOrAllParam, PerPageParam, QueueID
from mcp_tracker.mcp.tools._access import check_queue_access, is_queue_allowed
from mcp_tracker.mcp.tools._pagination import collect_pages
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.pagination import PaginatedResult
from mcp_tracker.tracker.proto.types.queues import (
    Queue,
    QueueExpandOption,
    QueueFieldsEnum,
    QueueVersion,
)

# `expand` sections that are lists, and so can meaningfully come back empty.
EXPAND_SECTIONS = frozenset(
    {"projects", "components", "versions", "types", "workflows", "fields"}
)


def register_queue_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register queue-related tools (all read-only)."""

    @mcp.tool(
        title="Get All Queues",
        description="Find all Yandex Tracker queues available to the user (queue is a project in some sense). "
        "Unlike other list tools, `page` here defaults to None and fetches ALL pages automatically - "
        "pass an explicit page number only if you hit the context size limit and want one page at a time.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queues_get_all(
        ctx: Context[Any, AppContext, Request],
        fields: Annotated[
            list[QueueFieldsEnum] | None,
            Field(
                description="Fields to include in the response. In order to not pollute context window - "
                "select appropriate fields beforehand. Not specifying fields returns ALL available fields "
                "(unlike project_find/portfolio_find/goal_find, which default to a small field subset). "
                "Most of the time one needs key and name only.",
            ),
        ] = None,
        page: PageOrAllParam = None,
        per_page: PerPageParam = 100,
    ) -> PaginatedResult[Queue]:
        def allowed(queues: list[Queue]) -> list[Queue]:
            return [
                queue
                for queue in queues
                if queue.key is not None and is_queue_allowed(settings, queue.key)
            ]

        result = await collect_pages(
            lambda current_page: (
                ctx.request_context.lifespan_context.queues.queues_list(
                    per_page=per_page,
                    page=current_page,
                    auth=get_yandex_auth(ctx),
                )
            ),
            page=page,
            per_page=per_page,
            visible=allowed,
            restricted=bool(settings.tracker_limit_queues),
        )

        if fields is not None:
            set_non_needed_fields_null(result.values, {f.name for f in fields})

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
        description="Get the fields configured on a specific Yandex Tracker queue, plus its local "
        "(queue-specific) fields by default. "
        "The schema.required property indicates whether a field is mandatory. "
        "Use this before creating an issue with issue_create - but note it is not the whole registry: "
        "system fields such as `parent`, `estimation` or `originalEstimation` are settable without "
        "appearing here, and `get_global_fields` lists every field the organization has.",
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
                "Use 'issueTypesConfig' to get available resolutions for each issue type. "
                "A requested section that the queue has nothing in comes back as an empty list."
            ),
        ] = None,
    ) -> Queue:
        check_queue_access(settings, queue_id)
        queue = await ctx.request_context.lifespan_context.queues.queue_get(
            queue_id,
            expand=expand,
            auth=get_yandex_auth(ctx),
        )

        # Tracker omits an expand section when the queue has nothing in it, which
        # reads the same as "expand did not work". Answer with an empty list so
        # the caller can tell the two apart.
        for option in expand or []:
            if option not in EXPAND_SECTIONS:
                continue
            if getattr(queue, option, None) is None:
                setattr(queue, option, [])

        return queue
