import datetime
from typing import Protocol

from .types.issues import Issue, IssueComment, IssueLink
from .types.queues import Queue


class QueuesProtocol(Protocol):
    async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]: ...
