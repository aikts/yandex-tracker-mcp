"""Component read-only MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.tools._access import check_component_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.components import Component


def register_component_read_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register component read-only tools."""

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
