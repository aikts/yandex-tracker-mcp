import datetime
from typing import Any, Protocol, runtime_checkable

from .common import YandexAuth
from .types.inputs import (
    IssueUpdateFollower,
    IssueUpdateParent,
    IssueUpdatePriority,
    IssueUpdateProject,
    IssueUpdateSprint,
    IssueUpdateType,
)
from .types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueTransition,
    Worklog,
)


@runtime_checkable
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
    async def issue_add_worklog(
        self,
        issue_id: str,
        *,
        duration: str,
        comment: str | None = None,
        start: datetime.datetime | None = None,
        auth: YandexAuth | None = None,
    ) -> Worklog: ...
    async def issue_update_worklog(
        self,
        issue_id: str,
        worklog_id: int,
        *,
        duration: str | None = None,
        comment: str | None = None,
        start: datetime.datetime | None = None,
        auth: YandexAuth | None = None,
    ) -> Worklog: ...
    async def issue_delete_worklog(
        self,
        issue_id: str,
        worklog_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...
    async def issue_get_attachments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueAttachment]: ...
    async def issues_count(
        self, query: str, *, auth: YandexAuth | None = None
    ) -> int: ...
    async def issue_get_checklist(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[ChecklistItem]: ...
    async def issue_create(
        self,
        queue: str,
        summary: str,
        *,
        type: int | None = None,
        description: str | None = None,
        assignee: str | int | None = None,
        priority: str | None = None,
        parent: str | None = None,
        sprint: list[str] | None = None,
        auth: YandexAuth | None = None,
        **kwargs: dict[str, Any],
    ) -> Issue: ...
    async def issue_get_transitions(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueTransition]: ...
    async def issue_execute_transition(
        self,
        issue_id: str,
        transition_id: str,
        *,
        comment: str | None = None,
        fields: dict[str, str | int | list[str]] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[IssueTransition]: ...

    async def issue_close(
        self,
        issue_id: str,
        resolution_id: str,
        *,
        comment: str | None = None,
        fields: dict[str, str | int | list[str]] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[IssueTransition]: ...

    async def issue_update(
        self,
        issue_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        markup_type: str | None = None,
        parent: IssueUpdateParent | None = None,
        sprint: list[IssueUpdateSprint] | None = None,
        type: IssueUpdateType | None = None,
        priority: IssueUpdatePriority | None = None,
        followers: list[IssueUpdateFollower] | None = None,
        project: IssueUpdateProject | None = None,
        attachment_ids: list[str] | None = None,
        description_attachment_ids: list[str] | None = None,
        tags: list[str] | None = None,
        version: int | None = None,
        auth: YandexAuth | None = None,
        **kwargs: Any,
    ) -> Issue: ...


class IssueProtocolWrap(IssueProtocol):
    def __init__(self, original: IssueProtocol):
        self._original = original
