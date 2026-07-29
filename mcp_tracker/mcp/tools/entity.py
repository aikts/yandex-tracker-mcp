"""Entity read MCP tools (projects, portfolios, goals) — all read-only."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageParam, PerPageParam
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import Entity, EntityType


def register_entity_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register entity read tools (all read-only)."""

    @mcp.tool(
        title="Get Entity",
        description=(
            "Get a Yandex Tracker entity (project, portfolio or goal) by id or shortId. "
            "Returns the entity with its fields (summary, entityStatus, ...)."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def entity_get(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity type: project, portfolio or goal"),
        ],
        entity_id: Annotated[
            str, Field(description="Entity id (long identifier) or shortId")
        ],
        fields: Annotated[
            str | None,
            Field(
                description="Comma-separated extra fields to include, e.g. 'summary,description'"
            ),
        ] = None,
        expand_attachments: Annotated[
            bool, Field(description="Include attached files in the response")
        ] = False,
    ) -> Entity:
        return await ctx.request_context.lifespan_context.entities.entity_get(
            entity_type,
            entity_id,
            fields=fields,
            expand_attachments=expand_attachments,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Find Entities",
        description=(
            "Find Yandex Tracker entities of a given type (project, portfolio or goal). "
            "Optionally filter by a name substring (input), field filters, and sort. "
            "Paginated: increase page until the result set is exhausted."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def entities_find(
        ctx: Context[Any, AppContext],
        entity_type: Annotated[
            EntityType,
            Field(description="Entity type: project, portfolio or goal"),
        ],
        input: Annotated[
            str | None,
            Field(description="Substring to match in the entity name"),
        ] = None,
        filter: Annotated[
            dict[str, Any] | None,
            Field(
                description='Field filters, e.g. {"entityStatus": "in_progress"}. '
                "Entity field keys may differ from issue field keys."
            ),
        ] = None,
        order_by: Annotated[
            str | None,
            Field(description="Field key to sort by"),
        ] = None,
        fields: Annotated[
            str | None,
            Field(
                description="Comma-separated extra fields to include in the response"
            ),
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> list[Entity]:
        return await ctx.request_context.lifespan_context.entities.entities_find(
            entity_type,
            input=input,
            filter=filter,
            order_by=order_by,
            fields=fields,
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )
