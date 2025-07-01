from typing import Protocol

from .common import YandexAuth
from .types.fields import GlobalField
from .types.issue_types import IssueType
from .types.priorities import Priority
from .types.statuses import Status


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


class GlobalDataProtocolWrap(GlobalDataProtocol):
    def __init__(self, original: GlobalDataProtocol):
        self._original = original
