from typing import Protocol, runtime_checkable

from .common import YandexAuth
from .types.fields import GlobalField
from .types.issue_types import IssueType
from .types.priorities import Priority
from .types.resolutions import Resolution
from .types.statuses import Status


@runtime_checkable
class GlobalDataProtocol(Protocol):
    async def get_global_fields(
        self, *, auth: YandexAuth | None = None
    ) -> list[GlobalField]: ...
    async def get_statuses(self, *, auth: YandexAuth | None = None) -> list[Status]: ...
    async def get_issue_types(
        self, *, auth: YandexAuth | None = None
    ) -> list[IssueType]: ...
    async def get_priorities(
        self, *, auth: YandexAuth | None = None
    ) -> list[Priority]: ...
    async def get_resolutions(
        self, *, auth: YandexAuth | None = None
    ) -> list[Resolution]: ...


class GlobalDataProtocolWrap(GlobalDataProtocol):
    def __init__(self, original: GlobalDataProtocol):
        self._original = original
