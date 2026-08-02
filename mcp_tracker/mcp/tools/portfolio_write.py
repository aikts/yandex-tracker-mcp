"""Portfolio write MCP tools (conditionally registered based on read-only mode)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    EntityClientsParam,
    EntityCommentParam,
    EntityDescriptionParam,
    EntityEndParam,
    EntityFollowersParam,
    EntityID,
    EntityLeadParam,
    EntityParentEntityParam,
    EntityStartParam,
    EntitySummaryParam,
    EntitySummaryRequiredParam,
    EntityTagsParam,
    EntityTeamAccessParam,
    EntityTeamUsersParam,
    EntityVersionParam,
    EntityWithBoardParam,
    PortfolioFieldsParam,
    ProjectPortfolioLinksParam,
    ProjectPortfolioStatusParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import PortfolioEntity

_QUEUE_RESTRICTIONS_NOTE = (
    " Not subject to TRACKER_LIMIT_QUEUES / TRACKER_READ_ONLY_QUEUES restrictions, "
    "since an entity isn't reliably mappable to a single queue."
)


def register_portfolio_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register portfolio write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Portfolio",
        description="Create a new Yandex Tracker portfolio." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_create(
        ctx: Context[Any, AppContext],
        summary: EntitySummaryRequiredParam,
        description: EntityDescriptionParam = None,
        lead: EntityLeadParam = None,
        team_users: EntityTeamUsersParam = None,
        clients: EntityClientsParam = None,
        followers: EntityFollowersParam = None,
        start: EntityStartParam = None,
        end: EntityEndParam = None,
        tags: EntityTagsParam = None,
        entity_status: ProjectPortfolioStatusParam = None,
        parent_entity: EntityParentEntityParam = None,
        team_access: EntityTeamAccessParam = None,
        links: ProjectPortfolioLinksParam = None,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_create(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=start,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
            links=links,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Portfolio",
        description="Update fields of an existing Yandex Tracker portfolio."
        + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_update(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        summary: EntitySummaryParam = None,
        description: EntityDescriptionParam = None,
        lead: EntityLeadParam = None,
        team_users: EntityTeamUsersParam = None,
        clients: EntityClientsParam = None,
        followers: EntityFollowersParam = None,
        start: EntityStartParam = None,
        end: EntityEndParam = None,
        tags: EntityTagsParam = None,
        entity_status: ProjectPortfolioStatusParam = None,
        parent_entity: EntityParentEntityParam = None,
        team_access: EntityTeamAccessParam = None,
        comment: EntityCommentParam = None,
        version: EntityVersionParam = None,
        links: ProjectPortfolioLinksParam = None,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_update(
            entity_id,
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=start,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
            comment=comment,
            version=version,
            links=links,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Portfolio",
        description="Delete a Yandex Tracker portfolio." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def portfolio_delete(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        with_board: EntityWithBoardParam = False,
    ) -> None:
        await ctx.request_context.lifespan_context.entities.portfolio_delete(
            entity_id,
            with_board=with_board,
            auth=get_yandex_auth(ctx),
        )
