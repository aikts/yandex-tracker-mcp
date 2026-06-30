from typing import Any, Protocol, runtime_checkable

from .common import YandexAuth
from .types.entities import Entity, EntityType


@runtime_checkable
class EntitiesProtocol(Protocol):
    async def entity_create(
        self,
        entity_type: EntityType,
        *,
        summary: str,
        fields: dict[str, Any] | None = None,
        auth: YandexAuth | None = None,
    ) -> Entity: ...

    async def entity_delete(
        self,
        entity_type: EntityType,
        entity_id: str,
        *,
        with_board: bool = False,
        auth: YandexAuth | None = None,
    ) -> None: ...
