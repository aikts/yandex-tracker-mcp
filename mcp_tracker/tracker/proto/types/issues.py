import datetime

from pydantic import AliasChoices, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity
from mcp_tracker.tracker.proto.types.mixins import CreatedUpdatedMixin
from mcp_tracker.tracker.proto.types.refs import (
    BaseReference,
    ComponentReference,
    IssueReference,
    IssueTypeReference,
    PriorityReference,
    QueueReference,
    StatusReference,
    UserReference,
)


class User(BaseTrackerEntity):
    display: str
    email: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    login: str
    uid: int


class Issue(CreatedUpdatedMixin, BaseTrackerEntity):
    unique: str | None = None
    key: str | None = None
    version: int | None = None
    summary: str
    description: str | None = None
    type: IssueTypeReference
    priority: PriorityReference | None = None
    assignee: UserReference | None = None
    status: StatusReference | None = None
    previous_status: StatusReference | None = Field(
        None, validation_alias=AliasChoices("previousStatus", "previous_status")
    )
    deadline: datetime.date | None = None
    components: list[ComponentReference] | None = None
    start: datetime.date | None = None
    end: datetime.date | None = None
    story_points: float | None = Field(
        None, validation_alias=AliasChoices("storyPoints", "story_points")
    )
    tags: list[str] = Field(default_factory=list)
    votes: int | None = None
    queue: QueueReference | None = None


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
