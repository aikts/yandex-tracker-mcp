from typing import Any, Protocol, runtime_checkable

from .common import YandexAuth
from .types.entities import Entity, EntityType


@runtime_checkable
class EntitiesProtocol(Protocol):
    async def entity_get(
        self,
        entity_type: EntityType,
        entity_id: str,
        *,
        fields: str | None = None,
        expand_attachments: bool = False,
        auth: YandexAuth | None = None,
    ) -> Entity: ...

    async def entities_find(
        self,
        entity_type: EntityType,
        *,
        input: str | None = None,
        filter: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        fields: str | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Entity]: ...

    async def entity_create(
        self,
        entity_type: EntityType,
        *,
        summary: str,
        fields: dict[str, Any] | None = None,
        links: list[dict[str, Any]] | None = None,
        auth: YandexAuth | None = None,
    ) -> Entity: ...

    async def entity_update(
        self,
        entity_type: EntityType,
        entity_id: str,
        *,
        fields: dict[str, Any] | None = None,
        comment: str | None = None,
        links: list[dict[str, Any]] | None = None,
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


class EntitiesProtocolWrap(EntitiesProtocol):
    def __init__(self, original: EntitiesProtocol):
        self._original = original
