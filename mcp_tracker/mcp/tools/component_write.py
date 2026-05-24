"""Component write MCP tools (conditionally registered based on read-only mode)."""

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
from mcp_tracker.tracker.proto.types.components import Component


def register_component_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register component write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Component",
        description="Create a new component in a Yandex Tracker queue. "
        "Components are used to categorize issues by service or module.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def component_create(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        name: Annotated[
            str,
            Field(description="Component name (e.g., 'Test', 'Monitoring')"),
        ],
        description: Annotated[
            str | None,
            Field(description="Optional component description"),
        ] = None,
        lead: Annotated[
            str | None,
            Field(
                description="Login (string) of the user responsible for this component"
            ),
        ] = None,
        assign_auto: Annotated[
            bool | None,
            Field(description="Automatically assign the component lead to issues"),
        ] = None,
    ) -> Component:
        check_queue_access(settings, queue_id)
        return await ctx.request_context.lifespan_context.components.component_create(
            queue_id,
            name=name,
            description=description,
            lead=lead,
            assign_auto=assign_auto,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Component",
        description="Update an existing component in Yandex Tracker.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def component_update(
        ctx: Context[Any, AppContext],
        component_id: Annotated[
            int,
            Field(description="Component ID (integer)."),
        ],
        name: Annotated[
            str | None,
            Field(description="New component name"),
        ] = None,
        description: Annotated[
            str | None,
            Field(description="New component description"),
        ] = None,
        lead: Annotated[
            str | None,
            Field(
                description="Login (string) of the user responsible for this component"
            ),
        ] = None,
    ) -> Component:
        return await ctx.request_context.lifespan_context.components.component_update(
            component_id,
            name=name,
            description=description,
            lead=lead,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Component",
        description="Delete a component from Yandex Tracker.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def component_delete(
        ctx: Context[Any, AppContext],
        component_id: Annotated[
            int,
            Field(description="Component ID (integer)."),
        ],
    ) -> None:
        await ctx.request_context.lifespan_context.components.component_delete(
            component_id,
            auth=get_yandex_auth(ctx),
        )
