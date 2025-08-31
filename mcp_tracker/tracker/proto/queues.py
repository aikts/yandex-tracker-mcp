from typing import Protocol, runtime_checkable

from .common import YandexAuth
from .types.fields import GlobalField, LocalField
from .types.queues import Queue, QueueExpandOption, QueueVersion


@runtime_checkable
class QueuesProtocol(Protocol):
    async def queues_list(
        self, per_page: int = 100, page: int = 1, *, auth: YandexAuth | None = None
    ) -> list[Queue]: ...

    async def queue_get(
        self,
        queue_id: str,
        *,
        expand: list[QueueExpandOption] | None = None,
        auth: YandexAuth | None = None,
    ) -> Queue: ...

    async def queues_get_local_fields(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[LocalField]: ...

    async def queues_get_tags(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[str]: ...

    async def queues_get_versions(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[QueueVersion]: ...

    async def queues_get_fields(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[GlobalField]: ...


class QueuesProtocolWrap(QueuesProtocol):
    def __init__(self, original: QueuesProtocol):
        self._original = original
