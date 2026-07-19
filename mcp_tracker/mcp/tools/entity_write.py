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
            "Entities group issues across queues. Place a project in a portfolio via "
            'fields.parentEntity ({"parentEntity": {"primary": "<portfolioId>"}}) or link '
            "it to a goal via links. Returns the created entity (id + shortId)."
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
                    '"start": "2026-01-01", "end": "2026-03-01"}. '
                    "To place a project in a portfolio: "
                    '{"parentEntity": {"primary": "<portfolioId>"}}.'
                ),
            ),
        ] = None,
        links: Annotated[
            list[dict[str, Any]] | None,
            Field(
                description=(
                    "Optional links to other entities, e.g. link a project to a goal: "
                    '[{"relationship": "works towards", "entity": "<goalId>"}]'
                ),
            ),
        ] = None,
    ) -> Entity:
        return await ctx.request_context.lifespan_context.entities.entity_create(
            entity_type,
            summary=summary,
            fields=fields,
            links=links,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Entity",
        description=(
            "Update a Yandex Tracker entity (project, portfolio or goal): rename, edit "
            "fields, and set relationships. Link a project/portfolio to a portfolio via "
            'fields.parentEntity ({"parentEntity": {"primary": "<portfolioId>"}}; use '
            '"secondary" for extra portfolios), or link to a goal via links.'
        ),
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def entity_update(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity type: project, portfolio or goal"),
        ],
        entity_id: Annotated[
            str, Field(description="Entity id (long identifier) or shortId")
        ],
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description=(
                    'Fields to change, e.g. {"summary": "...", "description": "..."}. '
                    'Link to a portfolio: {"parentEntity": {"primary": "<portfolioId>"}}.'
                ),
            ),
        ] = None,
        comment: Annotated[
            str | None, Field(description="Optional comment for the change")
        ] = None,
        links: Annotated[
            list[dict[str, Any]] | None,
            Field(
                description=(
                    "Links to other entities, e.g. to a goal: "
                    '[{"relationship": "works towards", "entity": "<goalId>"}]'
                ),
            ),
        ] = None,
    ) -> Entity:
        return await ctx.request_context.lifespan_context.entities.entity_update(
            entity_type,
            entity_id,
            fields=fields,
            comment=comment,
            links=links,
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
