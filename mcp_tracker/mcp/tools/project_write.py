"""Project write MCP tools (conditionally registered based on read-only mode)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    EntityClientsParam,
    EntityCommentIDParam,
    EntityCommentMaillistSummoneesParam,
    EntityCommentParam,
    EntityCommentSummoneesParam,
    EntityCommentTextParam,
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
    ProjectFieldsParam,
    ProjectPortfolioLinksParam,
    ProjectPortfolioStatusParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import ProjectEntity
from mcp_tracker.tracker.proto.types.issues import IssueComment

_QUEUE_RESTRICTIONS_NOTE = (
    " Not subject to TRACKER_LIMIT_QUEUES / TRACKER_READ_ONLY_QUEUES restrictions, "
    "since an entity isn't reliably mappable to a single queue."
)


def register_project_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register project write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Project",
        description="Create a new Yandex Tracker project." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def project_create(
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
        fields: ProjectFieldsParam = None,
    ) -> ProjectEntity:
        return await ctx.request_context.lifespan_context.entities.project_create(
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
        title="Update Project",
        description="Update fields of an existing Yandex Tracker project."
        + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def project_update(
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
        fields: ProjectFieldsParam = None,
    ) -> ProjectEntity:
        return await ctx.request_context.lifespan_context.entities.project_update(
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
        title="Delete Project",
        description="Delete a Yandex Tracker project." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def project_delete(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        with_board: EntityWithBoardParam = False,
    ) -> None:
        await ctx.request_context.lifespan_context.entities.project_delete(
            entity_id,
            with_board=with_board,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Project Comment",
        description="Add a comment to a Yandex Tracker project, e.g. entity_id='abc123'. "
        "IMPORTANT: If you need to mention/call people to the discussion (so they get "
        "notifications), do NOT rely on '@login' in the text — use the `summonees` "
        "parameter instead." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def project_add_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        text: EntityCommentTextParam,
        summonees: EntityCommentSummoneesParam = None,
        maillist_summonees: EntityCommentMaillistSummoneesParam = None,
    ) -> IssueComment:
        return await ctx.request_context.lifespan_context.entities.project_add_comment(
            entity_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Project Comment",
        description="Update an existing comment on a Yandex Tracker project. "
        "IMPORTANT: If you need to mention/call people (notifications), use the "
        "`summonees` parameter." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def project_update_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        comment_id: EntityCommentIDParam,
        text: EntityCommentTextParam,
        summonees: EntityCommentSummoneesParam = None,
        maillist_summonees: EntityCommentMaillistSummoneesParam = None,
    ) -> IssueComment:
        return (
            await ctx.request_context.lifespan_context.entities.project_update_comment(
                entity_id,
                comment_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=get_yandex_auth(ctx),
            )
        )

    @mcp.tool(
        title="Delete Project Comment",
        description="Delete a comment from a Yandex Tracker project."
        + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def project_delete_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        comment_id: EntityCommentIDParam,
    ) -> None:
        return (
            await ctx.request_context.lifespan_context.entities.project_delete_comment(
                entity_id,
                comment_id,
                auth=get_yandex_auth(ctx),
            )
        )
