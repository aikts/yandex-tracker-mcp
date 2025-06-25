from typing import Protocol

from .types.fields import LocalField
from .types.queues import Queue


class QueuesProtocol(Protocol):
    async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]: ...

    async def queues_get_local_fields(self, queue_id: str) -> list[LocalField]: ...

    async def queues_get_tags(self, queue_id: str) -> list[str]: ...


class QueuesProtocolWrap(QueuesProtocol):
    def __init__(self, original: QueuesProtocol):
        self._original = original
