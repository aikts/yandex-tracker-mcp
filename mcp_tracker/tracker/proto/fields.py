from typing import Protocol

from .types.fields import GlobalField
from .types.issue_types import IssueType
from .types.statuses import Status


class GlobalDataProtocol(Protocol):
    async def get_global_fields(self) -> list[GlobalField]: ...
    async def get_statuses(self) -> list[Status]: ...
    async def get_issue_types(self) -> list[IssueType]: ...


class GlobalDataProtocolWrap(GlobalDataProtocol):
    def __init__(self, original: GlobalDataProtocol):
        self._original = original
