from typing import Protocol

from .types.queues import Queue


class QueuesProtocol(Protocol):
    async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]: ...


class QueuesProtocolWrap(QueuesProtocol):
    def __init__(self, original: QueuesProtocol):
        self._original = original
