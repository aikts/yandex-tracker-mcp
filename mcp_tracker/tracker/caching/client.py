import datetime
from typing import Any

from aiocache import cached

from mcp_tracker.tracker.proto.issues import IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocolWrap
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.queues import Queue


def make_cached_protocols(
    cache_config: dict[str, Any],
) -> tuple[type[QueuesProtocolWrap], type[IssueProtocolWrap]]:
    class CachingQueuesProtocol(QueuesProtocolWrap):
        @cached(**cache_config)
        async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]:
            return await self._original.queues_list(per_page=per_page, page=page)

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
            queue: str,
            *,
            created_from: datetime.datetime | None = None,
            created_to: datetime.datetime | None = None,
            per_page: int = 15,
            page: int = 1,
        ) -> list[Issue]:
            return await self._original.issues_find(
                queue=queue,
                created_from=created_from,
                created_to=created_to,
                per_page=per_page,
                page=page,
            )

        @cached(**cache_config)
        async def issue_get_worklogs(self, issue_id: str) -> list[Worklog] | None:
            return await self._original.issue_get_worklogs(issue_id)

    return CachingQueuesProtocol, CachingIssuesProtocol
