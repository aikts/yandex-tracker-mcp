"""Goal write MCP tools (conditionally registered based on read-only mode)."""

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
    EntitySummaryParam,
    EntitySummaryRequiredParam,
    EntityTagsParam,
    EntityTeamAccessParam,
    EntityTeamUsersParam,
    EntityVersionParam,
    EntityWithBoardParam,
    GoalFieldsParam,
    GoalLinksParam,
    GoalStatusParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import GoalEntity
from mcp_tracker.tracker.proto.types.issues import IssueComment

_QUEUE_RESTRICTIONS_NOTE = (
    " Not subject to TRACKER_LIMIT_QUEUES / TRACKER_READ_ONLY_QUEUES restrictions, "
    "since an entity isn't reliably mappable to a single queue."
)


def register_goal_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register goal write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Goal",
        description="Create a new Yandex Tracker goal." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def goal_create(
        ctx: Context[Any, AppContext],
        summary: EntitySummaryRequiredParam,
        description: EntityDescriptionParam = None,
        lead: EntityLeadParam = None,
        team_users: EntityTeamUsersParam = None,
        clients: EntityClientsParam = None,
        followers: EntityFollowersParam = None,
        end: EntityEndParam = None,
        tags: EntityTagsParam = None,
        entity_status: GoalStatusParam = None,
        parent_entity: EntityParentEntityParam = None,
        team_access: EntityTeamAccessParam = None,
        links: GoalLinksParam = None,
        fields: GoalFieldsParam = None,
    ) -> GoalEntity:
        return await ctx.request_context.lifespan_context.entities.goal_create(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
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
        title="Update Goal",
        description="Update fields of an existing Yandex Tracker goal."
        + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def goal_update(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        summary: EntitySummaryParam = None,
        description: EntityDescriptionParam = None,
        lead: EntityLeadParam = None,
        team_users: EntityTeamUsersParam = None,
        clients: EntityClientsParam = None,
        followers: EntityFollowersParam = None,
        end: EntityEndParam = None,
        tags: EntityTagsParam = None,
        entity_status: GoalStatusParam = None,
        parent_entity: EntityParentEntityParam = None,
        team_access: EntityTeamAccessParam = None,
        comment: EntityCommentParam = None,
        version: EntityVersionParam = None,
        links: GoalLinksParam = None,
        fields: GoalFieldsParam = None,
    ) -> GoalEntity:
        return await ctx.request_context.lifespan_context.entities.goal_update(
            entity_id,
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
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
        title="Delete Goal",
        description="Delete a Yandex Tracker goal." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def goal_delete(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        with_board: EntityWithBoardParam = False,
    ) -> None:
        await ctx.request_context.lifespan_context.entities.goal_delete(
            entity_id,
            with_board=with_board,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Goal Comment",
        description="Add a comment to a Yandex Tracker goal, e.g. entity_id='ghi789'. "
        "IMPORTANT: If you need to mention/call people to the discussion (so they get "
        "notifications), do NOT rely on '@login' in the text — use the `summonees` "
        "parameter instead." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def goal_add_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        text: EntityCommentTextParam,
        summonees: EntityCommentSummoneesParam = None,
        maillist_summonees: EntityCommentMaillistSummoneesParam = None,
    ) -> IssueComment:
        return await ctx.request_context.lifespan_context.entities.goal_add_comment(
            entity_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Goal Comment",
        description="Update an existing comment on a Yandex Tracker goal. "
        "IMPORTANT: If you need to mention/call people (notifications), use the "
        "`summonees` parameter." + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def goal_update_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        comment_id: EntityCommentIDParam,
        text: EntityCommentTextParam,
        summonees: EntityCommentSummoneesParam = None,
        maillist_summonees: EntityCommentMaillistSummoneesParam = None,
    ) -> IssueComment:
        return await ctx.request_context.lifespan_context.entities.goal_update_comment(
            entity_id,
            comment_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Goal Comment",
        description="Delete a comment from a Yandex Tracker goal."
        + _QUEUE_RESTRICTIONS_NOTE,
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def goal_delete_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        comment_id: EntityCommentIDParam,
    ) -> None:
        return await ctx.request_context.lifespan_context.entities.goal_delete_comment(
            entity_id,
            comment_id,
            auth=get_yandex_auth(ctx),
        )
