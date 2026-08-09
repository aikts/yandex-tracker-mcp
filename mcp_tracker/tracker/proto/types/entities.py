from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.issues import ChecklistItem
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
    checklistItems: list[ChecklistItem] | None = NoneExcludedField


ProjectFieldsEnum = Enum(  # type: ignore[misc]
    "ProjectFieldsEnum",
    {key: key for key in ProjectFields.model_fields.keys()},
)


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
    checklistItems: list[ChecklistItem] | None = NoneExcludedField


PortfolioFieldsEnum = Enum(  # type: ignore[misc]
    "PortfolioFieldsEnum",
    {key: key for key in PortfolioFields.model_fields.keys()},
)


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


GoalFieldsEnum = Enum(  # type: ignore[misc]
    "GoalFieldsEnum",
    {key: key for key in GoalFields.model_fields.keys()},
)

# Base (non-custom) entity fields requested by default when the caller does not
# specify a `fields` list. Yandex Tracker only includes fields explicitly listed
# in the `fields` query parameter in the response's `fields` object.
#
# The sets differ per entity type: `start` exists only on projects and
# portfolios, so requesting it for a goal is not valid per the API docs.
DEFAULT_PROJECT_FIELDS = [
    "summary",
    "description",
    "entityStatus",
    "start",
    "end",
    "lead",
    "author",
    "tags",
]
DEFAULT_PORTFOLIO_FIELDS = DEFAULT_PROJECT_FIELDS
DEFAULT_GOAL_FIELDS = [
    "summary",
    "description",
    "entityStatus",
    "end",
    "lead",
    "author",
    "tags",
]

DEFAULT_ENTITY_FIELDS: dict[str, list[str]] = {
    "project": DEFAULT_PROJECT_FIELDS,
    "portfolio": DEFAULT_PORTFOLIO_FIELDS,
    "goal": DEFAULT_GOAL_FIELDS,
}
DEFAULT_ENTITY_FIELDS_PARAM: dict[str, str] = {
    entity_type: ",".join(entity_fields)
    for entity_type, entity_fields in DEFAULT_ENTITY_FIELDS.items()
}


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
