"""Component read-only MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PerPageParam, QueueID
from mcp_tracker.mcp.tools._access import check_component_access, check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.components import Component


def register_component_read_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register component read-only tools."""

    @mcp.tool(
        title="Get All Components",
        description="Get components in the Yandex Tracker organization. "
        "Supports pagination; omit page to retrieve all pages. "
        "Optionally filter by queue key.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def components_get_all(
        ctx: Context[Any, AppContext],
        queue_id: QueueID | None = None,
        page: Annotated[
            int | None,
            Field(
                description="Page number to return, default is None which means to retrieve all pages. "
                "Specify page number to retrieve a specific page when context limit is reached.",
                ge=1,
            ),
        ] = None,
        per_page: PerPageParam = 50,
    ) -> list[Component]:
        if queue_id is not None:
            check_queue_access(settings, queue_id)

        result: list[Component] = []

        fetch_all_pages = page is None
        if fetch_all_pages:
            page = 1

        # At this point page is always an int
        assert page is not None

        components_client = ctx.request_context.lifespan_context.components
        while True:
            components = await components_client.components_list(
                per_page=per_page,
                page=page,
                auth=get_yandex_auth(ctx),
            )
            if len(components) == 0:
                break

            result.extend(components)

            if not fetch_all_pages:
                break  # Only fetch the requested page
            page += 1

        if queue_id is not None:
            result = [
                component
                for component in result
                if component.queue is not None and component.queue.key == queue_id
            ]

        if settings.tracker_limit_queues:
            allowed_queues = set(settings.tracker_limit_queues)
            result = [
                component
                for component in result
                if component.queue is not None and component.queue.key in allowed_queues
            ]

        return result

    @mcp.tool(
        title="Get Component",
        description="Get a component from Yandex Tracker by its ID.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def component_get(
        ctx: Context[Any, AppContext],
        component_id: Annotated[
            int,
            Field(description="Component ID (integer)."),
        ],
    ) -> Component:
        component = await ctx.request_context.lifespan_context.components.component_get(
            component_id,
            auth=get_yandex_auth(ctx),
        )
        check_component_access(settings, component)
        return component
