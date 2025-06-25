from typing import Protocol

from .types.fields import GlobalField
from .types.statuses import Status


class GlobalDataProtocol(Protocol):
    async def get_global_fields(self) -> list[GlobalField]: ...
    async def get_statuses(self) -> list[Status]: ...


class GlobalDataProtocolWrap(GlobalDataProtocol):
    def __init__(self, original: GlobalDataProtocol):
        self._original = original
