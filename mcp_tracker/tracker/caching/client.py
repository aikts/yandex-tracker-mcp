from typing import Any

from aiocache import cached

from mcp_tracker.tracker.proto.fields import GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocolWrap
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.queues import Queue
from mcp_tracker.tracker.proto.types.statuses import Status


def make_cached_protocols(
    cache_config: dict[str, Any],
) -> tuple[
    type[QueuesProtocolWrap], type[IssueProtocolWrap], type[GlobalDataProtocolWrap]
]:
    class CachingQueuesProtocol(QueuesProtocolWrap):
        @cached(**cache_config)
        async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]:
            return await self._original.queues_list(per_page=per_page, page=page)

        @cached(**cache_config)
        async def queues_get_local_fields(self, queue_id: str) -> list[LocalField]:
            return await self._original.queues_get_local_fields(queue_id)

    class CachingIssuesProtocol(IssueProtocolWrap):
        @cached(**cache_config)
        async def issue_get(self, issue_id: str) -> Issue | None:
            return await self._original.issue_get(issue_id)

        @cached(**cache_config)
        async def issues_get_links(self, issue_id: str) -> list[IssueLink] | None:
            return await self._original.issues_get_links(issue_id)

        @cached(**cache_config)
        async def issue_get_comments(self, issue_id: str) -> list[IssueComment] | None:
            return await self._original.issue_get_comments(issue_id)

        @cached(**cache_config)
        async def issues_find(
            self,
            query: str,
            *,
            per_page: int = 15,
            page: int = 1,
        ) -> list[Issue]:
            return await self._original.issues_find(
                query=query,
                per_page=per_page,
                page=page,
            )

        @cached(**cache_config)
        async def issue_get_worklogs(self, issue_id: str) -> list[Worklog] | None:
            return await self._original.issue_get_worklogs(issue_id)

    class CachingGlobalDataProtocol(GlobalDataProtocolWrap):
        @cached(**cache_config)
        async def get_global_fields(self) -> list[GlobalField]:
            return await self._original.get_global_fields()

        @cached(**cache_config)
        async def get_statuses(self) -> list[Status]:
            return await self._original.get_statuses()

        @cached(**cache_config)
        async def get_issue_types(self) -> list[IssueType]:
            return await self._original.get_issue_types()

    return CachingQueuesProtocol, CachingIssuesProtocol, CachingGlobalDataProtocol
