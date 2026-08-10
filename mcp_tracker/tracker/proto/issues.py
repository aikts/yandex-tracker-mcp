import datetime
from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from .common import YandexAuth
from .types.inputs import (
    IssueComponentRef,
    IssueFollowerRef,
    IssueParentRef,
    IssuePriorityRef,
    IssueProjectRef,
    IssueSprintRef,
    IssueTypeRef,
)
from .types.issues import (
    ChangelogPage,
    ChecklistItem,
    CommentsPage,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueLinkRelationship,
    IssueTransition,
    Worklog,
)


@runtime_checkable
class IssueProtocol(Protocol):
    async def issue_get(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> Issue: ...
    async def issue_get_comments(
        self,
        issue_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage: ...
    async def issue_add_comment(
        self,
        issue_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        markup_type: str | None = None,
        is_add_to_followers: bool = True,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...
    async def issue_update_comment(
        self,
        issue_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        markup_type: str | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment: ...
    async def issue_delete_comment(
        self,
        issue_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...
    async def issues_get_links(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueLink]: ...
    async def issue_add_link(
        self,
        issue_id: str,
        *,
        relationship: IssueLinkRelationship,
        issue: str,
        auth: YandexAuth | None = None,
    ) -> IssueLink: ...
    async def issue_delete_link(
        self,
        issue_id: str,
        link_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...
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
        type: IssueTypeRef | str | int | None = None,
        description: str | None = None,
        markup_type: str | None = None,
        assignee: str | int | None = None,
        priority: IssuePriorityRef | str | int | None = None,
        parent: IssueParentRef | str | None = None,
        sprint: Sequence[IssueSprintRef | str | int] | None = None,
        followers: list[IssueFollowerRef] | None = None,
        components: list[IssueComponentRef] | None = None,
        tags: list[str] | None = None,
        project: IssueProjectRef | None = None,
        auth: YandexAuth | None = None,
        fields: dict[str, Any] | None = None,
    ) -> Issue: ...
    async def issue_get_transitions(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueTransition]: ...
    async def issue_get_changelog(
        self,
        issue_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        field: str | None = None,
        type: str | None = None,
        auth: YandexAuth | None = None,
    ) -> ChangelogPage: ...
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
        parent: IssueParentRef | str | None = None,
        sprint: Sequence[IssueSprintRef | str | int] | None = None,
        type: IssueTypeRef | str | int | None = None,
        priority: IssuePriorityRef | str | int | None = None,
        assignee: str | int | None = None,
        followers: list[IssueFollowerRef] | None = None,
        components: list[IssueComponentRef] | None = None,
        project: IssueProjectRef | None = None,
        attachment_ids: list[str] | None = None,
        description_attachment_ids: list[str] | None = None,
        tags: list[str] | None = None,
        version: int | None = None,
        auth: YandexAuth | None = None,
        fields: dict[str, Any] | None = None,
    ) -> Issue: ...

    async def issue_move(
        self,
        issue_id: str,
        queue: str,
        *,
        notify: bool = True,
        notify_author: bool = False,
        move_all_fields: bool = False,
        initial_status: bool = False,
        auth: YandexAuth | None = None,
    ) -> Issue: ...


class IssueProtocolWrap(IssueProtocol):
    def __init__(self, original: IssueProtocol):
        self._original = original
