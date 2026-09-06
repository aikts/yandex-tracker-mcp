from typing import Protocol, runtime_checkable

from .common import YandexAuth
from .types.components import Component


@runtime_checkable
class ComponentsProtocol(Protocol):
    async def component_get(
        self, component_id: int, *, auth: YandexAuth | None = None
    ) -> Component: ...

    async def component_create(
        self,
        queue_id: str,
        *,
        name: str,
        description: str | None = None,
        lead: str | None = None,
        assign_auto: bool | None = None,
        auth: YandexAuth | None = None,
    ) -> Component: ...

    async def component_update(
        self,
        component_id: int,
        *,
        version: int,
        name: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        assign_auto: bool | None = None,
        clear_lead: bool = False,
        auth: YandexAuth | None = None,
    ) -> Component: ...

    async def component_delete(
        self, component_id: int, *, auth: YandexAuth | None = None
    ) -> None: ...


class ComponentsProtocolWrap(ComponentsProtocol):
    def __init__(self, original: ComponentsProtocol):
        self._original = original
