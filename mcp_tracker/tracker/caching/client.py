import datetime
from dataclasses import dataclass
from typing import Any

from aiocache import cached

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.fields import GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocolWrap
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.inputs import (
    IssueUpdateFollower,
    IssueUpdateParent,
    IssueUpdatePriority,
    IssueUpdateProject,
    IssueUpdateSprint,
    IssueUpdateType,
)
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueTransition,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import (
    Queue,
    QueueExpandOption,
    QueueVersion,
)
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User
from mcp_tracker.tracker.proto.users import UsersProtocolWrap


@dataclass
class CacheCollection:
    queues: type[QueuesProtocolWrap]
    issues: type[IssueProtocolWrap]
    global_data: type[GlobalDataProtocolWrap]
    users: type[UsersProtocolWrap]


def make_cached_protocols(
    cache_config: dict[str, Any],
) -> CacheCollection:
    class CachingQueuesProtocol(QueuesProtocolWrap):
        @cached(**cache_config)
        async def queues_list(
            self, per_page: int = 100, page: int = 1, *, auth: YandexAuth | None = None
        ) -> list[Queue]:
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

        @cached(**cache_config)
        async def issue_get_comments(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[IssueComment]:
            return await self._original.issue_get_comments(issue_id, auth=auth)

        @cached(**cache_config)
        async def issues_find(
            self,
            query: str,
            *,
            per_page: int = 15,
            page: int = 1,
            auth: YandexAuth | None = None,
        ) -> list[Issue]:
            return await self._original.issues_find(
                query=query,
                per_page=per_page,
                page=page,
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
            type: int | None = None,
            description: str | None = None,
            assignee: str | int | None = None,
            priority: str | None = None,
            parent: str | None = None,
            sprint: list[str] | None = None,
            auth: YandexAuth | None = None,
            **kwargs: dict[str, Any],
        ) -> Issue:
            return await self._original.issue_create(
                queue,
                summary,
                type=type,
                description=description,
                assignee=assignee,
                priority=priority,
                parent=parent,
                sprint=sprint,
                auth=auth,
                **kwargs,
            )

        @cached(**cache_config)
        async def issue_get_transitions(
            self, issue_id: str, *, auth: YandexAuth | None = None
        ) -> list[IssueTransition]:
            return await self._original.issue_get_transitions(issue_id, auth=auth)

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
            parent: IssueUpdateParent | None = None,
            sprint: list[IssueUpdateSprint] | None = None,
            type: IssueUpdateType | None = None,
            priority: IssueUpdatePriority | None = None,
            followers: list[IssueUpdateFollower] | None = None,
            project: IssueUpdateProject | None = None,
            attachment_ids: list[str] | None = None,
            description_attachment_ids: list[str] | None = None,
            tags: list[str] | None = None,
            version: int | None = None,
            auth: YandexAuth | None = None,
            **kwargs: Any,
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
                followers=followers,
                project=project,
                attachment_ids=attachment_ids,
                description_attachment_ids=description_attachment_ids,
                tags=tags,
                version=version,
                auth=auth,
                **kwargs,
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

    class CachingUsersProtocol(UsersProtocolWrap):
        @cached(**cache_config)
        async def users_list(
            self, per_page: int = 50, page: int = 1, *, auth: YandexAuth | None = None
        ) -> list[User]:
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

    return CacheCollection(
        queues=CachingQueuesProtocol,
        issues=CachingIssuesProtocol,
        global_data=CachingGlobalDataProtocol,
        users=CachingUsersProtocol,
    )
