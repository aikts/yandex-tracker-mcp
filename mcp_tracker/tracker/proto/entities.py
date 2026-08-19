import datetime
from typing import Any, Protocol, runtime_checkable

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import (
    GoalEntity,
    GoalSearchResult,
    GoalStatus,
    PortfolioEntity,
    PortfolioSearchResult,
    ProjectEntity,
    ProjectPortfolioStatus,
    ProjectSearchResult,
)
from mcp_tracker.tracker.proto.types.inputs import (
    EntityChecklistItemUpdateInput,
    EntityParentEntityInput,
    GoalLinkInput,
    ProjectPortfolioLinkInput,
)
from mcp_tracker.tracker.proto.types.issues import CommentsPage, IssueComment


@runtime_checkable
class EntitiesProtocol(Protocol):
    async def project_get(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_find(
        self,
        *,
        input: str | None = None,
        filter: dict[str, str | list[str]] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectSearchResult: ...

    async def portfolio_get(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_find(
        self,
        *,
        input: str | None = None,
        filter: dict[str, str | list[str]] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioSearchResult: ...

    async def goal_get(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalEntity: ...

    async def goal_find(
        self,
        *,
        input: str | None = None,
        filter: dict[str, str | list[str]] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalSearchResult: ...

    async def project_create(
        self,
        *,
        summary: str,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_update(
        self,
        entity_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        comment: str | None = None,
        version: int | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_delete(
        self,
        entity_id: str,
        *,
        with_board: bool = False,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def portfolio_create(
        self,
        *,
        summary: str,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_update(
        self,
        entity_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        comment: str | None = None,
        version: int | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_delete(
        self,
        entity_id: str,
        *,
        with_board: bool = False,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def goal_create(
        self,
        *,
        summary: str,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: GoalStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[GoalLinkInput] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalEntity: ...

    async def goal_update(
        self,
        entity_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: GoalStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[GoalLinkInput] | None = None,
        comment: str | None = None,
        version: int | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalEntity: ...

    async def goal_delete(
        self,
        entity_id: str,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def project_get_comments(
        self,
        entity_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage: ...

    async def project_add_comment(
        self,
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...

    async def project_update_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...

    async def project_delete_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def portfolio_get_comments(
        self,
        entity_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage: ...

    async def portfolio_add_comment(
        self,
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...

    async def portfolio_update_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...

    async def portfolio_delete_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def goal_get_comments(
        self,
        entity_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage: ...

    async def goal_add_comment(
        self,
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...

    async def goal_update_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...

    async def goal_delete_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def project_add_checklist_item(
        self,
        entity_id: str,
        *,
        text: str,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_update_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        text: str | None = None,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_move_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        before: str,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_delete_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_update_checklist(
        self,
        entity_id: str,
        *,
        items: list[EntityChecklistItemUpdateInput],
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def project_delete_checklist(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity: ...

    async def portfolio_add_checklist_item(
        self,
        entity_id: str,
        *,
        text: str,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_update_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        text: str | None = None,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_move_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        before: str,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_delete_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_update_checklist(
        self,
        entity_id: str,
        *,
        items: list[EntityChecklistItemUpdateInput],
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...

    async def portfolio_delete_checklist(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity: ...


class EntitiesProtocolWrap(EntitiesProtocol):
    def __init__(self, original: EntitiesProtocol):
        self._original = original
