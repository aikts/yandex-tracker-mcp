from typing import Protocol

from .common import YandexAuth
from .types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)


class IssueProtocol(Protocol):
    async def issue_get(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> Issue: ...
    async def issue_get_comments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueComment]: ...
    async def issues_get_links(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueLink]: ...
    async def issues_find(
        self,
        query: str,
        *,
        per_page: int = 15,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[Issue]: ...
    async def issue_get_worklogs(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Worklog]: ...
    async def issue_get_attachments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueAttachment]: ...
    async def issues_count(
        self, query: str, *, auth: YandexAuth | None = None
    ) -> int: ...
    async def issue_get_checklist(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[ChecklistItem]: ...


class IssueProtocolWrap(IssueProtocol):
    def __init__(self, original: IssueProtocol):
        self._original = original
