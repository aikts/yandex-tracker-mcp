import datetime
from enum import Enum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity
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
        extra="ignore",
    )

    unique: str | None = None
    key: str | None = None
    summary: str | None = None
    description: str | None = None
    type: IssueTypeReference | None = None
    priority: PriorityReference | None = None
    assignee: UserReference | None = None
    status: StatusReference | None = None
    previous_status: StatusReference | None = Field(
        None, validation_alias=AliasChoices("previousStatus", "previous_status")
    )
    deadline: datetime.date | None = None
    components: list[ComponentReference] | None = None
    start: datetime.date | None = None
    story_points: float | None = Field(
        None, validation_alias=AliasChoices("storyPoints", "story_points")
    )
    tags: list[str] | None = None
    votes: int | None = None
    sprint: list[SprintReference] | None = None
    epic: IssueReference | None = None
    parent: IssueReference | None = None
    estimation: str | None = None
    spent: str | None = None


IssueFieldsEnum = Enum(  # type: ignore[misc]
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
