"""Queue component write MCP tools (conditionally registered based on read-only mode)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    ComponentAssignAutoParam,
    ComponentClearLeadParam,
    ComponentDescriptionParam,
    ComponentID,
    ComponentLeadParam,
    ComponentNameOptionalParam,
    ComponentNameParam,
    ComponentVersionParam,
    QueueID,
)
from mcp_tracker.mcp.tools._access import (
    check_component_access,
    check_queue_access,
    queue_checks_needed,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.components import Component


def register_component_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register queue component write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Component",
        description="Create a component (in russian - 'компонент') in a Yandex "
        "Tracker queue - a label grouping the queue's issues by product, process or "
        "owner; `lead` is a user login.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def component_create(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
        name: ComponentNameParam,
        description: ComponentDescriptionParam = None,
        lead: ComponentLeadParam = None,
        assign_auto: ComponentAssignAutoParam = None,
    ) -> Component:
        check_queue_access(settings, queue_id, write=True)
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
        description="Change the name, description, lead or auto-assign flag of a "
        "Yandex Tracker queue component (in russian - 'компонент'); omitted fields "
        "keep their value, `clear_lead` removes the lead.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def component_update(
        ctx: Context[Any, AppContext],
        component_id: ComponentID,
        name: ComponentNameOptionalParam = None,
        description: ComponentDescriptionParam = None,
        lead: ComponentLeadParam = None,
        assign_auto: ComponentAssignAutoParam = None,
        clear_lead: ComponentClearLeadParam = False,
        version: ComponentVersionParam = None,
    ) -> Component:
        components = ctx.request_context.lifespan_context.components
        auth = get_yandex_auth(ctx)

        # One read at most, for the version and/or the queue to check.
        if version is None or queue_checks_needed(settings, write=True):
            component = await components.component_get(component_id, auth=auth)
            check_component_access(settings, component, write=True)
            if version is None:
                version = component.version

        return await components.component_update(
            component_id,
            version=version,
            name=name,
            description=description,
            lead=lead,
            assign_auto=assign_auto,
            clear_lead=clear_lead,
            auth=auth,
        )

    @mcp.tool(
        title="Delete Component",
        description="Delete a Yandex Tracker queue component (in russian - "
        "'компонент') by its numeric id. Cannot be undone.",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def component_delete(
        ctx: Context[Any, AppContext],
        component_id: ComponentID,
    ) -> None:
        components = ctx.request_context.lifespan_context.components
        auth = get_yandex_auth(ctx)

        # Read the component only when there is a queue restriction to check.
        if queue_checks_needed(settings, write=True):
            component = await components.component_get(component_id, auth=auth)
            check_component_access(settings, component, write=True)

        await components.component_delete(component_id, auth=auth)
