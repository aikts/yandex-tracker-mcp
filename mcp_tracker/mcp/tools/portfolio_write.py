"""Portfolio write MCP tools (conditionally registered based on read-only mode)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    EntityChecklistItemAssigneeParam,
    EntityChecklistItemBeforeParam,
    EntityChecklistItemCheckedParam,
    EntityChecklistItemDeadlineParam,
    EntityChecklistItemIDParam,
    EntityChecklistItemsParam,
    EntityChecklistItemTextOptionalParam,
    EntityChecklistItemTextParam,
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
    PortfolioFieldsParam,
    ProjectPortfolioLinksParam,
    ProjectPortfolioStatusParam,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.entities import PortfolioEntity
from mcp_tracker.tracker.proto.types.issues import IssueComment


def register_portfolio_write_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register portfolio write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Create Portfolio",
        description="Create a new Yandex Tracker portfolio.",
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
        description="Update fields of an existing Yandex Tracker portfolio.",
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
        description="Delete a Yandex Tracker portfolio.",
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

    @mcp.tool(
        title="Add Portfolio Comment",
        description="Add a comment to a Yandex Tracker portfolio, e.g. entity_id='def456'. "
        "IMPORTANT: If you need to mention/call people to the discussion (so they get "
        "notifications), do NOT rely on '@login' in the text — use the `summonees` "
        "parameter instead.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_add_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        text: EntityCommentTextParam,
        summonees: EntityCommentSummoneesParam = None,
        maillist_summonees: EntityCommentMaillistSummoneesParam = None,
    ) -> IssueComment:
        return (
            await ctx.request_context.lifespan_context.entities.portfolio_add_comment(
                entity_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=get_yandex_auth(ctx),
            )
        )

    @mcp.tool(
        title="Update Portfolio Comment",
        description="Update an existing comment on a Yandex Tracker portfolio. "
        "IMPORTANT: If you need to mention/call people (notifications), use the "
        "`summonees` parameter.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_update_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        comment_id: EntityCommentIDParam,
        text: EntityCommentTextParam,
        summonees: EntityCommentSummoneesParam = None,
        maillist_summonees: EntityCommentMaillistSummoneesParam = None,
    ) -> IssueComment:
        return await ctx.request_context.lifespan_context.entities.portfolio_update_comment(
            entity_id,
            comment_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Portfolio Comment",
        description="Delete a comment from a Yandex Tracker portfolio.",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def portfolio_delete_comment(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        comment_id: EntityCommentIDParam,
    ) -> None:
        return await ctx.request_context.lifespan_context.entities.portfolio_delete_comment(
            entity_id,
            comment_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Portfolio Checklist Item",
        description="Add a checklist item to a Yandex Tracker portfolio, e.g. "
        "entity_id='def456'. Returns the full updated entity; request "
        "`checklistItems` via `fields` to see the new item.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_add_checklist_item(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        text: EntityChecklistItemTextParam,
        checked: EntityChecklistItemCheckedParam = None,
        assignee: EntityChecklistItemAssigneeParam = None,
        deadline: EntityChecklistItemDeadlineParam = None,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_add_checklist_item(
            entity_id,
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=deadline,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Portfolio Checklist Item",
        description="Update (partial) a checklist item on a Yandex Tracker portfolio.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_update_checklist_item(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        checklist_item_id: EntityChecklistItemIDParam,
        text: EntityChecklistItemTextOptionalParam = None,
        checked: EntityChecklistItemCheckedParam = None,
        assignee: EntityChecklistItemAssigneeParam = None,
        deadline: EntityChecklistItemDeadlineParam = None,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_update_checklist_item(
            entity_id,
            checklist_item_id,
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=deadline,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Move Portfolio Checklist Item",
        description="Reorder a checklist item on a Yandex Tracker portfolio by moving it "
        "before another item.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_move_checklist_item(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        checklist_item_id: EntityChecklistItemIDParam,
        before: EntityChecklistItemBeforeParam,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_move_checklist_item(
            entity_id,
            checklist_item_id,
            before=before,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Portfolio Checklist Item",
        description="Delete a single checklist item from a Yandex Tracker portfolio.",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def portfolio_delete_checklist_item(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        checklist_item_id: EntityChecklistItemIDParam,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_delete_checklist_item(
            entity_id,
            checklist_item_id,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Portfolio Checklist",
        description="Bulk-edit the existing checklist items of a Yandex Tracker portfolio. "
        "Pass every item the checklist currently has, each referencing an existing item "
        "`id`: a partial list is rejected by the API with a 500 error, and the item count "
        "cannot change. Use *_add_checklist_item / *_delete_checklist_item to add or "
        "remove items.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def portfolio_update_checklist(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        items: EntityChecklistItemsParam,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_update_checklist(
            entity_id,
            items=items,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Portfolio Checklist",
        description="Delete the entire checklist from a Yandex Tracker portfolio.",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def portfolio_delete_checklist(
        ctx: Context[Any, AppContext],
        entity_id: EntityID,
        fields: PortfolioFieldsParam = None,
    ) -> PortfolioEntity:
        return await ctx.request_context.lifespan_context.entities.portfolio_delete_checklist(
            entity_id,
            fields=[f.value for f in fields] if fields is not None else None,
            auth=get_yandex_auth(ctx),
        )
