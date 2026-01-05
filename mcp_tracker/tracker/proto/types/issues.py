import datetime
from enum import Enum

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
        exclude_if=none_excluder,
    )
    deadline: datetime.date | None = NoneExcludedField
    components: list[ComponentReference] | None = NoneExcludedField
    start: datetime.date | None = NoneExcludedField
    story_points: float | None = Field(
        None,
        validation_alias=AliasChoices("storyPoints", "story_points"),
        exclude_if=none_excluder,
    )
    tags: list[str] | None = NoneExcludedField
    votes: int | None = NoneExcludedField
    sprint: list[SprintReference] | None = NoneExcludedField
    epic: IssueReference | None = NoneExcludedField
    parent: IssueReference | None = NoneExcludedField
    estimation: str | None = NoneExcludedField
    spent: str | None = NoneExcludedField


IssueFieldsEnum = Enum(  # type: ignore[misc]  # ty: ignore[unused-ignore-comment]
    "IssueFieldsEnum",
    {key: key for key in Issue.model_fields.keys()},
)


class IssueComment(CreatedUpdatedMixin, BaseTrackerEntity):
    id: int
    long_id: str | None = Field(
        None, validation_alias=AliasChoices("longId", "long_id")
    )
    text: str | None = None
    transport: str | None = None
    text_html: str | None = Field(
        None, validation_alias=AliasChoices("textHtml", "text_html")
    )


class LinkTypeReference(BaseReference):
    id: str
    inward: str | None = None
    outward: str | None = None


class IssueLink(CreatedUpdatedMixin, BaseTrackerEntity):
    id: int
    direction: str | None = None
    type: LinkTypeReference | None = None
    object: IssueReference | None = None
    assignee: UserReference | None = None
    status: StatusReference | None = None


class Worklog(CreatedUpdatedMixin, BaseTrackerEntity):
    id: int
    start: datetime.datetime | None = None
    duration: datetime.timedelta | None = None
    issue: IssueReference | None = None
    comment: str | None = None


class IssueAttachment(CreatedMixin, BaseTrackerEntity):
    id: str
    name: str
    content: str | None = None
    size: int | None = None
    mimetype: str | None = Field(
        None, validation_alias=AliasChoices("mimeType", "mimetype")
    )
    metadata: dict[str, str] | None = None


class ChecklistItemDeadline(BaseModel):
    date: datetime.datetime
    deadline_type: str = Field(
        validation_alias=AliasChoices("deadlineType", "deadline_type")
    )
    is_exceeded: bool = Field(
        validation_alias=AliasChoices("isExceeded", "is_exceeded")
    )


class ChecklistItem(BaseTrackerEntity):
    id: str
    text: str
    text_html: str | None = Field(
        None, validation_alias=AliasChoices("textHtml", "text_html")
    )
    checked: bool = False
    assignee: UserReference | None = None
    deadline: ChecklistItemDeadline | None = None
    checklist_item_type: str | None = Field(
        None, validation_alias=AliasChoices("checklistItemType", "checklist_item_type")
    )


class IssueTransition(BaseTrackerEntity):
    """Represents a possible status transition for an issue."""

    id: str
    display: str | None = None
    to: StatusReference | None = None
