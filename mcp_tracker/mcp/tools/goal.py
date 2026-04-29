"""Goal-entity MCP tools (read + write).

Goals are part of the Yandex Tracker unified entities API
(`/v3/entities/goal/...`). They are not regular issues — they live in their own
namespace alongside projects and portfolios. See
https://yandex.ru/support/tracker/ru/concepts/entities/about-entities

Field reference (all optional unless noted, accepted in `fields` payload of
create/update):
- summary (str, required on create) — name
- description (str)
- end (str `YYYY-MM-DD`) — deadline
- entityStatus (str) — workflow status (`draft`, `achieved`, `cancelled`, ...)
- lead (str login or {id}) — responsible person
- teamUsers / clients / followers (lists of user refs)
- tags (list[str])
- parentEntity ({id, entityType}) — parent goal/project/portfolio
- teamAccess (bool)
- keyResultItems / metricItems — key results and metrics
"""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import PageParam, PerPageParam
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.goals import Goal


def register_goal_read_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register read-only goal tools."""

    @mcp.tool(
        title="Get Goal",
        description=(
            "Get a single Yandex Tracker goal entity by its id. "
            "By default the API returns only meta fields (id, version, entityType, timestamps); "
            "pass `fields` to receive editable attributes such as summary, description, end (deadline), "
            "entityStatus, lead, teamUsers, clients, followers, tags, parentEntity, teamAccess."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def goal_get(
        ctx: Context[Any, AppContext, Request],
        goal_id: Annotated[
            str,
            Field(
                description="Goal entity ID (24-char hex string), e.g., '69f1f551a5a4a076a93df775'."
            ),
        ],
        fields: Annotated[
            list[str] | None,
            Field(
                description="List of attribute names to include. Common: summary, description, end, "
                "entityStatus, lead, teamUsers, clients, followers, tags, parentEntity, teamAccess, "
                "keyResultItems, metricItems. Pass None to get only meta fields."
            ),
        ] = None,
    ) -> Goal:
        return await ctx.request_context.lifespan_context.goals.goal_get(
            goal_id,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Search Goals",
        description=(
            "Search Yandex Tracker goals via POST /v3/entities/goal/_search. "
            "Returns a list of goal entities. Use `input` for free-text search, "
            "or `filter` to pass a structured filter object (e.g., {'createdBy': 'login'}). "
            "Pass `fields` to populate attributes in the result."
        ),
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def goals_search(
        ctx: Context[Any, AppContext, Request],
        input: Annotated[
            str | None,
            Field(description="Free-text search query."),
        ] = None,
        filter: Annotated[
            dict[str, Any] | None,
            Field(description="Structured filter object passed through to the API."),
        ] = None,
        order_by: Annotated[
            str | None,
            Field(description="Field name to sort by (e.g., 'createdAt')."),
        ] = None,
        order_asc: Annotated[
            bool | None,
            Field(description="Sort direction. True = ASC, False = DESC."),
        ] = None,
        root_only: Annotated[
            bool | None,
            Field(description="If True — only root goals (no parent)."),
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 50,
        fields: Annotated[
            list[str] | None,
            Field(
                description="Attribute names to include in each hit (e.g., ['summary','end','entityStatus','lead'])."
            ),
        ] = None,
    ) -> list[Goal]:
        return await ctx.request_context.lifespan_context.goals.goals_search(
            input=input,
            filter=filter,
            order_by=order_by,
            order_asc=order_asc,
            root_only=root_only,
            per_page=per_page,
            page=page,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )


def register_goal_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register write goal tools (create/update/delete)."""

    @mcp.tool(
        title="Create Goal",
        description=(
            "Create a new goal entity in Yandex Tracker. "
            "Minimum required field is `summary`. Common optional fields: "
            "description, end (YYYY-MM-DD deadline), entityStatus, lead (user login or {id}), "
            "teamUsers, clients, followers, tags, parentEntity, teamAccess. "
            "Returns the created goal with id and shortId."
        ),
    )
    async def goal_create(
        ctx: Context[Any, AppContext, Request],
        summary: Annotated[
            str,
            Field(description="Goal name (required)."),
        ],
        description: Annotated[
            str | None,
            Field(description="Goal description (Markdown supported)."),
        ] = None,
        end: Annotated[
            str | None,
            Field(description="Deadline date in 'YYYY-MM-DD' format."),
        ] = None,
        entity_status: Annotated[
            str | None,
            Field(
                description="Workflow status, e.g., 'draft', 'achieved', 'cancelled'. "
                "Defaults to 'draft' if omitted."
            ),
        ] = None,
        lead: Annotated[
            str | None,
            Field(
                description="Responsible person — user login or UID. Defaults to the authenticated user."
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Field(description="List of tag strings."),
        ] = None,
        parent_entity_id: Annotated[
            str | None,
            Field(
                description="Parent entity id (another goal/project/portfolio). "
                "Pair with parent_entity_type."
            ),
        ] = None,
        parent_entity_type: Annotated[
            str | None,
            Field(
                description="Parent entity type: 'goal', 'project', or 'portfolio'."
            ),
        ] = None,
        extra_fields: Annotated[
            dict[str, Any] | None,
            Field(
                description="Additional fields to merge into the request payload. "
                "Use this to set teamUsers, clients, followers, teamAccess, keyResultItems, metricItems, etc."
            ),
        ] = None,
    ) -> Goal:
        fields: dict[str, Any] = {"summary": summary}
        if description is not None:
            fields["description"] = description
        if end is not None:
            fields["end"] = end
        if entity_status is not None:
            fields["entityStatus"] = entity_status
        if lead is not None:
            fields["lead"] = lead
        if tags is not None:
            fields["tags"] = tags
        if parent_entity_id is not None:
            parent: dict[str, Any] = {"id": parent_entity_id}
            if parent_entity_type is not None:
                parent["entityType"] = parent_entity_type
            fields["parentEntity"] = parent
        if extra_fields:
            for k, v in extra_fields.items():
                fields.setdefault(k, v)

        return await ctx.request_context.lifespan_context.goals.goal_create(
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Goal",
        description=(
            "Update an existing goal via PATCH /v3/entities/goal/{id}. "
            "Pass only the fields you want to change. "
            "NB: if any single field value is rejected, the whole patch is rolled back (HTTP 422)."
        ),
    )
    async def goal_update(
        ctx: Context[Any, AppContext, Request],
        goal_id: Annotated[
            str,
            Field(description="Goal entity ID (24-char hex string)."),
        ],
        fields: Annotated[
            dict[str, Any],
            Field(
                description="Object of fields to update. Example: "
                "{'summary': 'New name', 'end': '2026-12-31', 'entityStatus': 'achieved'}."
            ),
        ],
        version: Annotated[
            int | None,
            Field(
                description="Optimistic-lock version. If provided and stale, the API returns 409."
            ),
        ] = None,
    ) -> Goal:
        return await ctx.request_context.lifespan_context.goals.goal_update(
            goal_id,
            fields=fields,
            version=version,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Goal",
        description="Delete a goal entity. Returns nothing (HTTP 204).",
    )
    async def goal_delete(
        ctx: Context[Any, AppContext, Request],
        goal_id: Annotated[
            str,
            Field(description="Goal entity ID (24-char hex string)."),
        ],
    ) -> None:
        await ctx.request_context.lifespan_context.goals.goal_delete(
            goal_id,
            auth=get_yandex_auth(ctx),
        )
