"""Entity write MCP tools (conditionally registered based on read-only mode)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import Entity, EntityType


def register_entity_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register entity write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Entity",
        description=(
            "Create a Yandex Tracker entity — a project, portfolio or goal. "
            "Entities group issues across queues. Returns the created entity, "
            "including its id (used for API calls) and shortId (shown in the UI)."
        ),
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def entity_create(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity type to create: project, portfolio or goal"),
        ],
        summary: Annotated[str, Field(description="Entity name (required)")],
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description=(
                    "Optional additional entity fields, for example: "
                    '{"lead": "<username>", "description": "<text>", '
                    '"start": "2026-01-01", "end": "2026-03-01"}'
                ),
            ),
        ] = None,
    ) -> Entity:
        return await ctx.request_context.lifespan_context.entities.entity_create(
            entity_type,
            summary=summary,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Entity",
        description=(
            "Delete a Yandex Tracker entity (project, portfolio or goal) by its id. "
            "Deletion is immediate and permanent."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def entity_delete(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity type: project, portfolio or goal"),
        ],
        entity_id: Annotated[
            str,
            Field(description="Entity id (the long identifier, not the shortId)"),
        ],
        with_board: Annotated[
            bool,
            Field(description="Also delete the board associated with the entity"),
        ] = False,
    ) -> None:
        await ctx.request_context.lifespan_context.entities.entity_delete(
            entity_type,
            entity_id,
            with_board=with_board,
            auth=get_yandex_auth(ctx),
        )
