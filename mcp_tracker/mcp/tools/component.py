"""Queue component MCP tools (read-only)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import ComponentID
from mcp_tracker.mcp.tools._access import check_component_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.components import Component


def register_component_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register queue component tools (all read-only)."""

    @mcp.tool(
        title="Get Component",
        description="Get one Yandex Tracker queue component (in russian - "
        "'компонент') by its numeric id, with `queue`, `lead`, `assignAuto` and the "
        "`version` that `component_update` takes. Ids come from "
        "`queue_get_components` or an issue's `components` field.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def component_get(
        ctx: Context[Any, AppContext],
        component_id: ComponentID,
    ) -> Component:
        component = await ctx.request_context.lifespan_context.components.component_get(
            component_id,
            auth=get_yandex_auth(ctx),
        )
        # The id names no queue, so the check runs on what came back.
        check_component_access(settings, component)
        return component
