from datetime import date, datetime
from typing import Literal

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.mixins import CreatedUpdatedMixin
from mcp_tracker.tracker.proto.types.refs import QueueReference, UserReference

# Status values for projects and portfolios.
ProjectPortfolioStatus = Literal[
    "draft",
    "draft2",
    "in_progress",
    "according_to_plan",
    "postponed",
    "at_risk",
    "blocked",
    "launched",
    "cancelled",
]

# Status values for goals.
GoalStatus = Literal[
    "draft",
    "according_to_plan",
    "at_risk",
    "blocked",
    "achieved",
    "partially_achieved",
    "not_achieved",
    "exceeded",
    "cancelled",
]

# Link relationship values for projects and portfolios.
ProjectPortfolioLinkRelationship = Literal[
    "depends on",
    "is dependent by",
    "works towards",
]

# Link relationship values for goals.
GoalLinkRelationship = Literal[
    "parent entity",
    "child entity",
    "depends on",
    "is dependent by",
    "is supported by",
]


class EntityReference(BaseTrackerEntity):
    """Reference to an entity returned inside another entity."""

    id: str | None = NoneExcludedField
    display: str | None = NoneExcludedField


class ParentEntityRef(BaseTrackerEntity):
    """Parent entities in the projects/portfolios/goals hierarchy."""

    primary: EntityReference | None = NoneExcludedField
    secondary: list[EntityReference] | None = NoneExcludedField


class ProjectFields(BaseTrackerEntity):
    """Explicit (non-dynamic) field set for a Yandex Tracker project.

    Only the base, non-custom fields are modeled here. Custom user-defined
    attributes are intentionally omitted for this initial version.
    """

    summary: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    lead: UserReference | None = NoneExcludedField
    author: UserReference | None = NoneExcludedField
    teamUsers: list[UserReference] | None = NoneExcludedField
    clients: list[UserReference] | None = NoneExcludedField
    followers: list[UserReference] | None = NoneExcludedField
    start: date | datetime | None = NoneExcludedField
    end: date | datetime | None = NoneExcludedField
    quarter: list[str] | None = NoneExcludedField
    tags: list[str] | None = NoneExcludedField
    entityStatus: ProjectPortfolioStatus | None = NoneExcludedField
    parentEntity: ParentEntityRef | None = NoneExcludedField
    teamAccess: bool | None = NoneExcludedField
    issueQueues: list[QueueReference] | None = NoneExcludedField
    lastCommentUpdatedAt: date | datetime | None = NoneExcludedField
    linkedGoalsCount: int | None = NoneExcludedField


class PortfolioFields(BaseTrackerEntity):
    """Explicit (non-dynamic) field set for a Yandex Tracker portfolio."""

    summary: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    lead: UserReference | None = NoneExcludedField
    author: UserReference | None = NoneExcludedField
    teamUsers: list[UserReference] | None = NoneExcludedField
    clients: list[UserReference] | None = NoneExcludedField
    followers: list[UserReference] | None = NoneExcludedField
    start: date | datetime | None = NoneExcludedField
    end: date | datetime | None = NoneExcludedField
    quarter: list[str] | None = NoneExcludedField
    tags: list[str] | None = NoneExcludedField
    entityStatus: ProjectPortfolioStatus | None = NoneExcludedField
    parentEntity: ParentEntityRef | None = NoneExcludedField
    teamAccess: bool | None = NoneExcludedField
    lastCommentUpdatedAt: date | datetime | None = NoneExcludedField
    linkedGoalsCount: int | None = NoneExcludedField


class GoalFields(BaseTrackerEntity):
    """Explicit (non-dynamic) field set for a Yandex Tracker goal."""

    summary: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    lead: UserReference | None = NoneExcludedField
    author: UserReference | None = NoneExcludedField
    teamUsers: list[UserReference] | None = NoneExcludedField
    clients: list[UserReference] | None = NoneExcludedField
    followers: list[UserReference] | None = NoneExcludedField
    end: date | datetime | None = NoneExcludedField
    tags: list[str] | None = NoneExcludedField
    entityStatus: GoalStatus | None = NoneExcludedField
    parentEntity: ParentEntityRef | None = NoneExcludedField
    teamAccess: bool | None = NoneExcludedField
    progressPercentage: float | None = NoneExcludedField
    lastCommentUpdatedAt: date | datetime | None = NoneExcludedField
    linkedProjectsCount: int | None = NoneExcludedField


class ProjectEntity(CreatedUpdatedMixin, BaseTrackerEntity):
    id: str | None = NoneExcludedField
    shortId: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    entityType: Literal["project"] | None = NoneExcludedField
    fields: ProjectFields | None = NoneExcludedField


class PortfolioEntity(CreatedUpdatedMixin, BaseTrackerEntity):
    id: str | None = NoneExcludedField
    shortId: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    entityType: Literal["portfolio"] | None = NoneExcludedField
    fields: PortfolioFields | None = NoneExcludedField


class GoalEntity(CreatedUpdatedMixin, BaseTrackerEntity):
    id: str | None = NoneExcludedField
    shortId: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    entityType: Literal["goal"] | None = NoneExcludedField
    fields: GoalFields | None = NoneExcludedField


class ProjectSearchResult(BaseTrackerEntity):
    hits: int | None = NoneExcludedField
    pages: int | None = NoneExcludedField
    values: list[ProjectEntity] = Field(default_factory=list)


class PortfolioSearchResult(BaseTrackerEntity):
    hits: int | None = NoneExcludedField
    pages: int | None = NoneExcludedField
    values: list[PortfolioEntity] = Field(default_factory=list)


class GoalSearchResult(BaseTrackerEntity):
    hits: int | None = NoneExcludedField
    pages: int | None = NoneExcludedField
    values: list[GoalEntity] = Field(default_factory=list)
