from typing import Protocol

from .types.queues import Queue


class QueuesProtocol(Protocol):
    async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]: ...
