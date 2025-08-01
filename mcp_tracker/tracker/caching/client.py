from typing import Any

from aiocache import cached

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.fields import GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocolWrap
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User
from mcp_tracker.tracker.proto.users import UsersProtocolWrap


def make_cached_protocols(
    cache_config: dict[str, Any],
) -> tuple[
    type[QueuesProtocolWrap],
    type[IssueProtocolWrap],
    type[GlobalDataProtocolWrap],
    type[UsersProtocolWrap],
]:
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

    return (
        CachingQueuesProtocol,
        CachingIssuesProtocol,
        CachingGlobalDataProtocol,
        CachingUsersProtocol,
    )
