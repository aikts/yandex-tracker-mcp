import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from mcp_tracker.tracker.proto.types.base import (
    BaseTrackerEntity,
    NoneExcludedField,
    none_excluder,
)
from mcp_tracker.tracker.proto.types.mixins import CreatedMixin, CreatedUpdatedMixin
from mcp_tracker.tracker.proto.types.refs import (
    BaseReference,
    ComponentReference,
    IssueReference,
    IssueTypeReference,
    PriorityReference,
    SprintReference,
    StatusReference,
    UserReference,
)


class Issue(CreatedUpdatedMixin, BaseTrackerEntity):
    model_config = ConfigDict(
        extra="allow",
    )
    version: int | None = NoneExcludedField
    unique: str | None = NoneExcludedField
    key: str | None = NoneExcludedField
    summary: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    type: IssueTypeReference | None = NoneExcludedField
    priority: PriorityReference | None = NoneExcludedField
    assignee: UserReference | None = NoneExcludedField
    status: StatusReference | None = NoneExcludedField
    previous_status: StatusReference | None = Field(
        None,
        validation_alias=AliasChoices("previousStatus", "previous_status"),
        serialization_alias="previousStatus",
        exclude_if=none_excluder,
    )
    deadline: datetime.date | None = NoneExcludedField
    components: list[ComponentReference] | None = NoneExcludedField
    start: datetime.date | None = NoneExcludedField
    story_points: float | None = Field(
        None,
        validation_alias=AliasChoices("storyPoints", "story_points"),
        serialization_alias="storyPoints",
        exclude_if=none_excluder,
    )
    tags: list[str] | None = NoneExcludedField
    votes: int | None = NoneExcludedField
    sprint: list[SprintReference] | None = NoneExcludedField
    epic: IssueReference | None = NoneExcludedField
    parent: IssueReference | None = NoneExcludedField
    estimation: str | None = NoneExcludedField
    spent: str | None = NoneExcludedField


IssueFieldsEnum = Enum(  # type: ignore[misc]
    "IssueFieldsEnum",
    {key: key for key in Issue.model_fields.keys()},
)


class MaillistReference(BaseReference):
    display: str | None = None


class IssueComment(CreatedUpdatedMixin, BaseTrackerEntity):
    id: int
    long_id: str | None = Field(
        None,
        validation_alias=AliasChoices("longId", "long_id"),
        serialization_alias="longId",
        exclude_if=none_excluder,
    )
    text: str | None = NoneExcludedField
    transport: str | None = NoneExcludedField
    text_html: str | None = Field(
        None,
        validation_alias=AliasChoices("textHtml", "text_html"),
        serialization_alias="textHtml",
        exclude_if=none_excluder,
    )
    summonees: list[UserReference] | None = Field(
        None,
        validation_alias=AliasChoices("summonees", "summonees"),
        exclude_if=none_excluder,
    )
    maillist_summonees: list[MaillistReference] | None = Field(
        None,
        validation_alias=AliasChoices("maillistSummonees", "maillist_summonees"),
        serialization_alias="maillistSummonees",
        exclude_if=none_excluder,
    )


CommentFieldsEnum = Enum(  # type: ignore[misc]
    "CommentFieldsEnum",
    {key: key for key in IssueComment.model_fields.keys()},
)


class LinkTypeReference(BaseReference):
    id: str
    inward: str | None = None
    outward: str | None = None


# Link relationship types accepted by the Yandex Tracker "link issue" API.
IssueLinkRelationship = Literal[
    "relates",
    "is dependent by",
    "depends on",
    "is subtask for",
    "is parent task for",
    "duplicates",
    "is duplicated by",
    "is epic of",
    "has epic",
]


class IssueLink(CreatedUpdatedMixin, BaseTrackerEntity):
    id: int
    direction: str | None = None
    type: LinkTypeReference | None = None
    object: IssueReference | None = None
    assignee: UserReference | None = None
    status: StatusReference | None = None


class Worklog(CreatedUpdatedMixin, BaseTrackerEntity):
    id: int
    start: datetime.datetime | None = NoneExcludedField
    duration: datetime.timedelta | None = NoneExcludedField
    issue: IssueReference | None = NoneExcludedField
    comment: str | None = NoneExcludedField


WorklogFieldsEnum = Enum(  # type: ignore[misc]
    "WorklogFieldsEnum",
    {key: key for key in Worklog.model_fields.keys()},
)


class IssueAttachment(CreatedMixin, BaseTrackerEntity):
    id: str
    name: str
    content: str | None = NoneExcludedField
    size: int | None = NoneExcludedField
    mimetype: str | None = Field(
        None,
        validation_alias=AliasChoices("mimeType", "mimetype"),
        serialization_alias="mimeType",
        exclude_if=none_excluder,
    )
    metadata: dict[str, str] | None = NoneExcludedField


AttachmentFieldsEnum = Enum(  # type: ignore[misc]
    "AttachmentFieldsEnum",
    {key: key for key in IssueAttachment.model_fields.keys()},
)


class ChecklistItemDeadline(BaseModel):
    date: datetime.datetime
    deadline_type: str = Field(
        validation_alias=AliasChoices("deadlineType", "deadline_type"),
        serialization_alias="deadlineType",
    )
    is_exceeded: bool = Field(
        validation_alias=AliasChoices("isExceeded", "is_exceeded"),
        serialization_alias="isExceeded",
    )


class ChecklistItem(BaseTrackerEntity):
    id: str
    text: str
    text_html: str | None = Field(
        None,
        validation_alias=AliasChoices("textHtml", "text_html"),
        serialization_alias="textHtml",
    )
    checked: bool = False
    assignee: UserReference | None = None
    deadline: ChecklistItemDeadline | None = None
    checklist_item_type: str | None = Field(
        None,
        validation_alias=AliasChoices("checklistItemType", "checklist_item_type"),
        serialization_alias="checklistItemType",
    )


class IssueTransition(BaseTrackerEntity):
    """Represents a possible status transition for an issue."""

    id: str
    display: str | None = None
    to: StatusReference | None = None


class ChangelogFieldReference(BaseReference):
    """Reference to the field that changed in a changelog entry (id + human-readable display)."""

    display: str | None = None


class ChangelogFieldChange(BaseTrackerEntity):
    """A single field change within a changelog entry (old value -> new value).

    `from`/`to` are intentionally untyped: Yandex Tracker returns a reference object
    for relation fields (status, assignee, ...), a plain string for text fields
    (summary, description, ...) or an array for collection fields (tags, components, ...).
    """

    field: ChangelogFieldReference | None = None
    from_: Any | None = Field(
        None,
        validation_alias=AliasChoices("from", "from_"),
        serialization_alias="from",
        exclude_if=none_excluder,
    )
    to: Any | None = NoneExcludedField


class ChangelogReference(BaseReference):
    """Reference to a sub-object (comment, trigger, ...) in a changelog entry (id + display)."""

    display: str | None = None


class ChangelogComments(BaseTrackerEntity):
    """Comment changes captured in a changelog entry (e.g. comments added).

    Modeled leniently (`extra="allow"`) so sibling keys the API may attach
    (`removed`, `changed`, ...) survive instead of being dropped.
    """

    model_config = ConfigDict(extra="allow")

    added: list[ChangelogReference] | None = NoneExcludedField


class ChangelogExecutedTrigger(BaseTrackerEntity):
    """A trigger executed as part of a changelog entry: which automation fired and its outcome."""

    trigger: ChangelogReference | None = None
    success: bool | None = None
    message: str | None = None


class ChangelogEntry(CreatedUpdatedMixin, BaseTrackerEntity):
    """A single entry of an issue change history: status transitions, field edits,
    comment changes, executed triggers, etc.

    `extra="allow"` so that documented top-level payloads the API attaches to specific
    change types but that are not modeled explicitly here (worklog/attachment/link/vote
    changes) pass through to the client instead of being silently dropped, matching the
    `Issue` model's passthrough behavior.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    issue: IssueReference | None = None
    type: str | None = None
    transport: str | None = None
    fields: list[ChangelogFieldChange] | None = None
    comments: ChangelogComments | None = NoneExcludedField
    executed_triggers: list[ChangelogExecutedTrigger] | None = Field(
        None,
        validation_alias=AliasChoices("executedTriggers", "executed_triggers"),
        serialization_alias="executedTriggers",
        exclude_if=none_excluder,
    )


class CommentsPage(BaseTrackerEntity):
    """A page of comments plus the cursor to fetch the next page.

    `next_cursor` is the cursor for the next page, or `None` when there are no more
    pages; how it is obtained depends on the endpoint. Pass it back as the `cursor`
    argument to continue.
    """

    comments: list[IssueComment]
    next_cursor: str | None = None


class ChangelogPage(BaseTrackerEntity):
    """A page of issue changelog entries plus the cursor to fetch the next page.

    `next_cursor` is parsed from the `Link: rel="next"` response header; it is `None`
    when there are no more pages. Pass it back as the `cursor` argument to continue.
    """

    entries: list[ChangelogEntry]
    next_cursor: str | None = None
