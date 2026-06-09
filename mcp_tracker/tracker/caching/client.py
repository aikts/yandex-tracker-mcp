import datetime
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiocache import cached

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.entities import EntitiesProtocolWrap
from mcp_tracker.tracker.proto.fields import GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocolWrap
from mcp_tracker.tracker.proto.templates import TemplatesProtocolWrap
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
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.inputs import (
    EntityChecklistItemUpdateInput,
    EntityParentEntityInput,
    GoalLinkInput,
    IssueComponentRef,
    IssueFollowerRef,
    IssueParentRef,
    IssuePriorityRef,
    IssueProjectRef,
    IssueSprintRef,
    IssueTypeRef,
    ProjectPortfolioLinkInput,
)
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChangelogPage,
    ChecklistItem,
    CommentsPage,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueLinkRelationship,
    IssueTransition,
    Worklog,
)
from mcp_tracker.tracker.proto.types.pagination import PaginatedResult
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import (
    Queue,
    QueueExpandOption,
    QueueVersion,
)
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.templates import CommentTemplate, IssueTemplate
from mcp_tracker.tracker.proto.types.users import User
from mcp_tracker.tracker.proto.users import UsersProtocolWrap


@dataclass
class CacheCollection:
    queues: type[QueuesProtocolWrap]
    issues: type[IssueProtocolWrap]
    global_data: type[GlobalDataProtocolWrap]
    templates: type[TemplatesProtocolWrap]
    users: type[UsersProtocolWrap]
    entities: type[EntitiesProtocolWrap]


def make_cached_protocols(
    cache_config: dict[str, Any],
) -> CacheCollection:
    class CachingQueuesProtocol(QueuesProtocolWrap):
        @cached(**cache_config)
        async def queues_list(
            self, per_page: int = 100, page: int = 1, *, auth: YandexAuth | None = None
        ) -> PaginatedResult[Queue]:
            return await self._original.queues_list(
                per_page=per_page, page=page, auth=auth
            )

        @cached(**cache_config)
        async def queues_get_local_fields(
            self, queue_id: str, *, auth: YandexAuth | None = None
        ) -> list[LocalField]:
            return await self._original.queues_get_local_fields(queue_id, auth=auth)

        @cached(**cache_config)
        async def queues_get_tags(
            self, queue_id: str, *, auth: YandexAuth | None = None
        ) -> list[str]:
            return await self._original.queues_get_tags(queue_id, auth=auth)

        @cached(**cache_config)
        async def queues_get_versions(
            self, queue_id: str, *, auth: YandexAuth | None = None
        ) -> list[QueueVersion]:
            return await self._original.queues_get_versions(queue_id, auth=auth)

        async def queue_create_version(
            self,
            queue_id: str,
            *,
            name: str,
            description: str | None = None,
            start_date: datetime.date | None = None,
            due_date: datetime.date | None = None,
            auth: YandexAuth | None = None,
        ) -> QueueVersion:
            return await self._original.queue_create_version(
                queue_id,
                name=name,
                description=description,
                start_date=start_date,
                due_date=due_date,
                auth=auth,
            )

        @cached(**cache_config)
        async def queues_get_fields(
            self, queue_id: str, *, auth: YandexAuth | None = None
        ) -> list[GlobalField]:
            return await self._original.queues_get_fields(queue_id, auth=auth)

        @cached(**cache_config)
        async def queue_get(
            self,
            queue_id: str,
            *,
            expand: list[QueueExpandOption] | None = None,
            auth: YandexAuth | None = None,
        ) -> Queue:
            return await self._original.queue_get(queue_id, expand=expand, auth=auth)

    class CachingIssuesProtocol(IssueProtocolWrap):
        @cached(**cache_config)
        async def issue_get(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> Issue:
            return await self._original.issue_get(issue_id, auth=auth)

        @cached(**cache_config)
        async def issues_get_links(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[IssueLink]:
            return await self._original.issues_get_links(issue_id, auth=auth)

        async def issue_add_link(
            self,
            issue_id: str,
            *,
            relationship: IssueLinkRelationship,
            issue: str,
            auth: YandexAuth | None = None,
        ) -> IssueLink:
            return await self._original.issue_add_link(
                issue_id,
                relationship=relationship,
                issue=issue,
                auth=auth,
            )

        async def issue_delete_link(
            self,
            issue_id: str,
            link_id: int,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.issue_delete_link(issue_id, link_id, auth=auth)

        @cached(**cache_config)
        async def issue_get_comments(
            self,
            issue_id: str,
            *,
            per_page: int = 50,
            cursor: str | None = None,
            auth: YandexAuth | None = None,
        ) -> CommentsPage:
            return await self._original.issue_get_comments(
                issue_id, per_page=per_page, cursor=cursor, auth=auth
            )

        async def issue_add_comment(
            self,
            issue_id: str,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            markup_type: str | None = None,
            is_add_to_followers: bool = True,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.issue_add_comment(
                issue_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                markup_type=markup_type,
                is_add_to_followers=is_add_to_followers,
                auth=auth,
            )

        async def issue_update_comment(
            self,
            issue_id: str,
            comment_id: int,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            markup_type: str | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.issue_update_comment(
                issue_id,
                comment_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                markup_type=markup_type,
                auth=auth,
            )

        async def issue_delete_comment(
            self,
            issue_id: str,
            comment_id: int,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.issue_delete_comment(
                issue_id, comment_id, auth=auth
            )

        @cached(**cache_config)
        async def issues_find(
            self,
            query: str,
            *,
            per_page: int = 15,
            page: int = 1,
            fields: Sequence[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> PaginatedResult[Issue]:
            return await self._original.issues_find(
                query=query,
                per_page=per_page,
                page=page,
                fields=fields,
                auth=auth,
            )

        @cached(**cache_config)
        async def issue_get_worklogs(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[Worklog]:
            return await self._original.issue_get_worklogs(issue_id, auth=auth)

        async def issue_add_worklog(
            self,
            issue_id: str,
            *,
            duration: str,
            comment: str | None = None,
            start: datetime.datetime | None = None,
            auth: YandexAuth | None = None,
        ) -> Worklog:
            return await self._original.issue_add_worklog(
                issue_id,
                duration=duration,
                comment=comment,
                start=start,
                auth=auth,
            )

        async def issue_update_worklog(
            self,
            issue_id: str,
            worklog_id: int,
            *,
            duration: str | None = None,
            comment: str | None = None,
            start: datetime.datetime | None = None,
            auth: YandexAuth | None = None,
        ) -> Worklog:
            return await self._original.issue_update_worklog(
                issue_id,
                worklog_id,
                duration=duration,
                comment=comment,
                start=start,
                auth=auth,
            )

        async def issue_delete_worklog(
            self,
            issue_id: str,
            worklog_id: int,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.issue_delete_worklog(
                issue_id,
                worklog_id,
                auth=auth,
            )

        @cached(**cache_config)
        async def issue_get_attachments(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[IssueAttachment]:
            return await self._original.issue_get_attachments(issue_id, auth=auth)

        async def issue_download_attachment(
            self,
            issue_id: str,
            attachment_id: str,
            file_name: str,
            destination: Path,
            max_bytes: int,
            *,
            auth: YandexAuth | None = None,
        ) -> int:
            return await self._original.issue_download_attachment(
                issue_id,
                attachment_id,
                file_name,
                destination,
                max_bytes,
                auth=auth,
            )

        @cached(**cache_config)
        async def issues_count(
            self, query: str, *, auth: YandexAuth | None = None
        ) -> int:
            return await self._original.issues_count(query, auth=auth)

        @cached(**cache_config)
        async def issue_get_checklist(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[ChecklistItem]:
            return await self._original.issue_get_checklist(issue_id, auth=auth)

        async def issue_create(
            self,
            queue: str,
            summary: str,
            *,
            type: IssueTypeRef | str | int | None = None,
            description: str | None = None,
            markup_type: str | None = None,
            assignee: str | int | None = None,
            priority: IssuePriorityRef | str | int | None = None,
            parent: IssueParentRef | str | None = None,
            sprint: Sequence[IssueSprintRef | str | int] | None = None,
            followers: list[IssueFollowerRef] | None = None,
            components: list[IssueComponentRef] | None = None,
            tags: list[str] | None = None,
            project: IssueProjectRef | None = None,
            auth: YandexAuth | None = None,
            fields: dict[str, Any] | None = None,
        ) -> Issue:
            return await self._original.issue_create(
                queue,
                summary,
                type=type,
                description=description,
                markup_type=markup_type,
                assignee=assignee,
                priority=priority,
                parent=parent,
                sprint=sprint,
                followers=followers,
                components=components,
                tags=tags,
                project=project,
                auth=auth,
                fields=fields,
            )

        @cached(**cache_config)
        async def issue_get_transitions(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[IssueTransition]:
            return await self._original.issue_get_transitions(issue_id, auth=auth)

        # Not cached: the changelog is an append-only, growing history. Caching the
        # first page (cursor=None) would keep serving a stale page that misses the
        # most recent changes until the TTL expires.
        async def issue_get_changelog(
            self,
            issue_id: str,
            *,
            per_page: int = 50,
            cursor: str | None = None,
            field: str | None = None,
            type: str | None = None,
            auth: YandexAuth | None = None,
        ) -> ChangelogPage:
            return await self._original.issue_get_changelog(
                issue_id,
                per_page=per_page,
                cursor=cursor,
                field=field,
                type=type,
                auth=auth,
            )

        async def issue_execute_transition(
            self,
            issue_id: str,
            transition_id: str,
            *,
            comment: str | None = None,
            fields: dict[str, str | int | list[str]] | None = None,
            auth: YandexAuth | None = None,
        ) -> list[IssueTransition]:
            return await self._original.issue_execute_transition(
                issue_id,
                transition_id,
                comment=comment,
                fields=fields,
                auth=auth,
            )

        async def issue_close(
            self,
            issue_id: str,
            resolution_id: str,
            *,
            comment: str | None = None,
            fields: dict[str, str | int | list[str]] | None = None,
            auth: YandexAuth | None = None,
        ) -> list[IssueTransition]:
            return await self._original.issue_close(
                issue_id,
                resolution_id,
                comment=comment,
                fields=fields,
                auth=auth,
            )

        async def issue_update(
            self,
            issue_id: str,
            *,
            summary: str | None = None,
            description: str | None = None,
            markup_type: str | None = None,
            parent: IssueParentRef | str | None = None,
            sprint: Sequence[IssueSprintRef | str | int] | None = None,
            type: IssueTypeRef | str | int | None = None,
            priority: IssuePriorityRef | str | int | None = None,
            assignee: str | int | None = None,
            followers: list[IssueFollowerRef] | None = None,
            components: list[IssueComponentRef] | None = None,
            project: IssueProjectRef | None = None,
            attachment_ids: list[str] | None = None,
            description_attachment_ids: list[str] | None = None,
            tags: list[str] | None = None,
            version: int | None = None,
            auth: YandexAuth | None = None,
            fields: dict[str, Any] | None = None,
        ) -> Issue:
            return await self._original.issue_update(
                issue_id,
                summary=summary,
                description=description,
                markup_type=markup_type,
                parent=parent,
                sprint=sprint,
                type=type,
                priority=priority,
                assignee=assignee,
                followers=followers,
                components=components,
                project=project,
                attachment_ids=attachment_ids,
                description_attachment_ids=description_attachment_ids,
                tags=tags,
                version=version,
                auth=auth,
                fields=fields,
            )

        async def issue_move(
            self,
            issue_id: str,
            queue: str,
            *,
            notify: bool = True,
            notify_author: bool = False,
            move_all_fields: bool = False,
            initial_status: bool = False,
            auth: YandexAuth | None = None,
        ) -> Issue:
            return await self._original.issue_move(
                issue_id,
                queue,
                notify=notify,
                notify_author=notify_author,
                move_all_fields=move_all_fields,
                initial_status=initial_status,
                auth=auth,
            )

    class CachingGlobalDataProtocol(GlobalDataProtocolWrap):
        @cached(**cache_config)
        async def get_global_fields(
            self, *, auth: YandexAuth | None = None
        ) -> list[GlobalField]:
            return await self._original.get_global_fields(auth=auth)

        @cached(**cache_config)
        async def get_statuses(self, *, auth: YandexAuth | None = None) -> list[Status]:
            return await self._original.get_statuses(auth=auth)

        @cached(**cache_config)
        async def get_issue_types(
            self, *, auth: YandexAuth | None = None
        ) -> list[IssueType]:
            return await self._original.get_issue_types(auth=auth)

        @cached(**cache_config)
        async def get_priorities(
            self, *, auth: YandexAuth | None = None
        ) -> list[Priority]:
            return await self._original.get_priorities(auth=auth)

        @cached(**cache_config)
        async def get_resolutions(
            self, *, auth: YandexAuth | None = None
        ) -> list[Resolution]:
            return await self._original.get_resolutions(auth=auth)

    class CachingTemplatesProtocol(TemplatesProtocolWrap):
        @cached(**cache_config)
        async def get_issue_templates(
            self,
            *,
            queue: str | None = None,
            per_page: int = 50,
            page: int = 1,
            auth: YandexAuth | None = None,
        ) -> PaginatedResult[IssueTemplate]:
            return await self._original.get_issue_templates(
                queue=queue, per_page=per_page, page=page, auth=auth
            )

        @cached(**cache_config)
        async def get_issue_template(
            self, template_id: str, *, auth: YandexAuth | None = None
        ) -> IssueTemplate:
            return await self._original.get_issue_template(template_id, auth=auth)

        @cached(**cache_config)
        async def get_comment_templates(
            self,
            *,
            queue: str | None = None,
            per_page: int = 50,
            page: int = 1,
            auth: YandexAuth | None = None,
        ) -> PaginatedResult[CommentTemplate]:
            return await self._original.get_comment_templates(
                queue=queue, per_page=per_page, page=page, auth=auth
            )

        @cached(**cache_config)
        async def get_comment_template(
            self, template_id: str, *, auth: YandexAuth | None = None
        ) -> CommentTemplate:
            return await self._original.get_comment_template(template_id, auth=auth)

    class CachingUsersProtocol(UsersProtocolWrap):
        @cached(**cache_config)
        async def users_list(
            self, per_page: int = 50, page: int = 1, *, auth: YandexAuth | None = None
        ) -> PaginatedResult[User]:
            return await self._original.users_list(
                per_page=per_page, page=page, auth=auth
            )

        @cached(**cache_config)
        async def user_get(
            self, user_id: str, *, auth: YandexAuth | None = None
        ) -> User | None:
            return await self._original.user_get(user_id, auth=auth)

        @cached(**cache_config)
        async def user_get_current(self, *, auth: YandexAuth | None = None) -> User:
            return await self._original.user_get_current(auth=auth)

    class CachingEntitiesProtocol(EntitiesProtocolWrap):
        @cached(**cache_config)
        async def project_get(
            self,
            entity_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> ProjectEntity:
            return await self._original.project_get(entity_id, fields=fields, auth=auth)

        @cached(**cache_config)
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
        ) -> ProjectSearchResult:
            return await self._original.project_find(
                input=input,
                filter=filter,
                order_by=order_by,
                order_asc=order_asc,
                root_only=root_only,
                per_page=per_page,
                page=page,
                fields=fields,
                auth=auth,
            )

        @cached(**cache_config)
        async def portfolio_get(
            self,
            entity_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> PortfolioEntity:
            return await self._original.portfolio_get(
                entity_id, fields=fields, auth=auth
            )

        @cached(**cache_config)
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
        ) -> PortfolioSearchResult:
            return await self._original.portfolio_find(
                input=input,
                filter=filter,
                order_by=order_by,
                order_asc=order_asc,
                root_only=root_only,
                per_page=per_page,
                page=page,
                fields=fields,
                auth=auth,
            )

        @cached(**cache_config)
        async def goal_get(
            self,
            entity_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> GoalEntity:
            return await self._original.goal_get(entity_id, fields=fields, auth=auth)

        @cached(**cache_config)
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
        ) -> GoalSearchResult:
            return await self._original.goal_find(
                input=input,
                filter=filter,
                order_by=order_by,
                order_asc=order_asc,
                root_only=root_only,
                per_page=per_page,
                page=page,
                fields=fields,
                auth=auth,
            )

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
        ) -> ProjectEntity:
            return await self._original.project_create(
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
                fields=fields,
                auth=auth,
            )

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
        ) -> ProjectEntity:
            return await self._original.project_update(
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
                links=links,
                comment=comment,
                version=version,
                fields=fields,
                auth=auth,
            )

        async def project_delete(
            self,
            entity_id: str,
            *,
            with_board: bool = False,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.project_delete(
                entity_id, with_board=with_board, auth=auth
            )

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
        ) -> PortfolioEntity:
            return await self._original.portfolio_create(
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
                fields=fields,
                auth=auth,
            )

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
        ) -> PortfolioEntity:
            return await self._original.portfolio_update(
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
                links=links,
                comment=comment,
                version=version,
                fields=fields,
                auth=auth,
            )

        async def portfolio_delete(
            self,
            entity_id: str,
            *,
            with_board: bool = False,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.portfolio_delete(
                entity_id, with_board=with_board, auth=auth
            )

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
        ) -> GoalEntity:
            return await self._original.goal_create(
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
                fields=fields,
                auth=auth,
            )

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
        ) -> GoalEntity:
            return await self._original.goal_update(
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
                links=links,
                comment=comment,
                version=version,
                fields=fields,
                auth=auth,
            )

        async def goal_delete(
            self,
            entity_id: str,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.goal_delete(entity_id, auth=auth)

        # Comments are never cached: they mutate frequently and caching would
        # risk serving stale conversation state.
        async def project_get_comments(
            self,
            entity_id: str,
            *,
            per_page: int = 50,
            cursor: str | None = None,
            auth: YandexAuth | None = None,
        ) -> CommentsPage:
            return await self._original.project_get_comments(
                entity_id, per_page=per_page, cursor=cursor, auth=auth
            )

        async def project_add_comment(
            self,
            entity_id: str,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.project_add_comment(
                entity_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=auth,
            )

        async def project_update_comment(
            self,
            entity_id: str,
            comment_id: int,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.project_update_comment(
                entity_id,
                comment_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=auth,
            )

        async def project_delete_comment(
            self,
            entity_id: str,
            comment_id: int,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.project_delete_comment(
                entity_id, comment_id, auth=auth
            )

        async def portfolio_get_comments(
            self,
            entity_id: str,
            *,
            per_page: int = 50,
            cursor: str | None = None,
            auth: YandexAuth | None = None,
        ) -> CommentsPage:
            return await self._original.portfolio_get_comments(
                entity_id, per_page=per_page, cursor=cursor, auth=auth
            )

        async def portfolio_add_comment(
            self,
            entity_id: str,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.portfolio_add_comment(
                entity_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=auth,
            )

        async def portfolio_update_comment(
            self,
            entity_id: str,
            comment_id: int,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.portfolio_update_comment(
                entity_id,
                comment_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=auth,
            )

        async def portfolio_delete_comment(
            self,
            entity_id: str,
            comment_id: int,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.portfolio_delete_comment(
                entity_id, comment_id, auth=auth
            )

        async def goal_get_comments(
            self,
            entity_id: str,
            *,
            per_page: int = 50,
            cursor: str | None = None,
            auth: YandexAuth | None = None,
        ) -> CommentsPage:
            return await self._original.goal_get_comments(
                entity_id, per_page=per_page, cursor=cursor, auth=auth
            )

        async def goal_add_comment(
            self,
            entity_id: str,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.goal_add_comment(
                entity_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=auth,
            )

        async def goal_update_comment(
            self,
            entity_id: str,
            comment_id: int,
            *,
            text: str,
            summonees: list[str] | None = None,
            maillist_summonees: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> IssueComment:
            return await self._original.goal_update_comment(
                entity_id,
                comment_id,
                text=text,
                summonees=summonees,
                maillist_summonees=maillist_summonees,
                auth=auth,
            )

        async def goal_delete_comment(
            self,
            entity_id: str,
            comment_id: int,
            *,
            auth: YandexAuth | None = None,
        ) -> None:
            return await self._original.goal_delete_comment(
                entity_id, comment_id, auth=auth
            )

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
        ) -> ProjectEntity:
            return await self._original.project_add_checklist_item(
                entity_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )

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
        ) -> ProjectEntity:
            return await self._original.project_update_checklist_item(
                entity_id,
                checklist_item_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )

        async def project_move_checklist_item(
            self,
            entity_id: str,
            checklist_item_id: str,
            *,
            before: str,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> ProjectEntity:
            return await self._original.project_move_checklist_item(
                entity_id,
                checklist_item_id,
                before=before,
                fields=fields,
                auth=auth,
            )

        async def project_delete_checklist_item(
            self,
            entity_id: str,
            checklist_item_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> ProjectEntity:
            return await self._original.project_delete_checklist_item(
                entity_id,
                checklist_item_id,
                fields=fields,
                auth=auth,
            )

        async def project_update_checklist(
            self,
            entity_id: str,
            *,
            items: list[EntityChecklistItemUpdateInput],
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> ProjectEntity:
            return await self._original.project_update_checklist(
                entity_id,
                items=items,
                fields=fields,
                auth=auth,
            )

        async def project_delete_checklist(
            self,
            entity_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> ProjectEntity:
            return await self._original.project_delete_checklist(
                entity_id, fields=fields, auth=auth
            )

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
        ) -> PortfolioEntity:
            return await self._original.portfolio_add_checklist_item(
                entity_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )

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
        ) -> PortfolioEntity:
            return await self._original.portfolio_update_checklist_item(
                entity_id,
                checklist_item_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )

        async def portfolio_move_checklist_item(
            self,
            entity_id: str,
            checklist_item_id: str,
            *,
            before: str,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> PortfolioEntity:
            return await self._original.portfolio_move_checklist_item(
                entity_id,
                checklist_item_id,
                before=before,
                fields=fields,
                auth=auth,
            )

        async def portfolio_delete_checklist_item(
            self,
            entity_id: str,
            checklist_item_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> PortfolioEntity:
            return await self._original.portfolio_delete_checklist_item(
                entity_id,
                checklist_item_id,
                fields=fields,
                auth=auth,
            )

        async def portfolio_update_checklist(
            self,
            entity_id: str,
            *,
            items: list[EntityChecklistItemUpdateInput],
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> PortfolioEntity:
            return await self._original.portfolio_update_checklist(
                entity_id,
                items=items,
                fields=fields,
                auth=auth,
            )

        async def portfolio_delete_checklist(
            self,
            entity_id: str,
            *,
            fields: list[str] | None = None,
            auth: YandexAuth | None = None,
        ) -> PortfolioEntity:
            return await self._original.portfolio_delete_checklist(
                entity_id, fields=fields, auth=auth
            )

    return CacheCollection(
        queues=CachingQueuesProtocol,
        issues=CachingIssuesProtocol,
        global_data=CachingGlobalDataProtocol,
        templates=CachingTemplatesProtocol,
        users=CachingUsersProtocol,
        entities=CachingEntitiesProtocol,
    )
