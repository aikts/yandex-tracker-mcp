"""Pydantic models for Yandex Tracker Goal entities.

Goals are part of the unified `/v3/entities/{type}` API alongside projects and
portfolios. This module models only the `goal` entity type. The shape mirrors
what the API returns: top-level meta fields (`id`, `version`, `entityType`,
timestamps, `createdBy`) plus a nested `fields` object that holds editable
attributes (`summary`, `description`, `end` deadline, `entityStatus`, `lead`,
team/clients/followers, tags, parent, etc.).
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import ConfigDict, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField


class GoalUserRef(BaseTrackerEntity):
    """User reference embedded inside Goal (lead/teamUsers/clients/followers)."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: str | None = NoneExcludedField
    display: str | None = NoneExcludedField
    cloudUid: str | None = NoneExcludedField
    passportUid: int | None = NoneExcludedField


class GoalParentEntityRef(BaseTrackerEntity):
    """Reference to a parent entity (another goal/project/portfolio)."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: str | None = NoneExcludedField
    entityType: str | None = NoneExcludedField
    display: str | None = NoneExcludedField


class GoalFields(BaseTrackerEntity):
    """Editable attributes of a Goal returned inside the `fields` envelope.

    All fields are optional because the API only returns those requested via
    the `?fields=` query parameter. The Tracker UI exposes more attributes
    (key results, metrics, weight, etc.) — those that can be set via REST are
    listed in the official documentation:
    https://yandex.ru/support/tracker/ru/concepts/entities/about-entities
    """

    model_config = ConfigDict(extra="allow")

    summary: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    end: date | None = NoneExcludedField
    entityStatus: str | None = NoneExcludedField
    lead: GoalUserRef | None = NoneExcludedField
    teamUsers: list[GoalUserRef] | None = NoneExcludedField
    clients: list[GoalUserRef] | None = NoneExcludedField
    followers: list[GoalUserRef] | None = NoneExcludedField
    tags: list[str] | None = NoneExcludedField
    parentEntity: GoalParentEntityRef | None = NoneExcludedField
    teamAccess: bool | None = NoneExcludedField
    keyResultItems: list[Any] | None = NoneExcludedField
    metricItems: list[Any] | None = NoneExcludedField
    lastCommentUpdatedAt: datetime | None = NoneExcludedField


class Goal(BaseTrackerEntity):
    """A Tracker Goal entity (`/v3/entities/goal/{id}`)."""

    model_config = ConfigDict(extra="ignore")

    self: str | None = NoneExcludedField
    id: str | None = NoneExcludedField
    version: int | None = NoneExcludedField
    shortId: int | None = NoneExcludedField
    entityType: Literal["goal"] | None = NoneExcludedField
    createdBy: GoalUserRef | None = NoneExcludedField
    createdAt: datetime | None = NoneExcludedField
    updatedAt: datetime | None = NoneExcludedField
    fields: GoalFields | None = NoneExcludedField


GoalFieldName = Literal[
    "summary",
    "description",
    "end",
    "entityStatus",
    "lead",
    "teamUsers",
    "clients",
    "followers",
    "tags",
    "parentEntity",
    "teamAccess",
    "keyResultItems",
    "metricItems",
    "lastCommentUpdatedAt",
]


GoalEntityStatus = Enum(  # type: ignore[misc]  # ty: ignore[unused-ignore-comment]
    "GoalEntityStatus",
    {
        "draft": "draft",
        "according_to_plan": "according_to_plan",
        "at_risk": "at_risk",
        "blocked": "blocked",
        "achieved": "achieved",
        "partially_achieved": "partially_achieved",
        "not_achieved": "not_achieved",
        "exceeded": "exceeded",
        "cancelled": "cancelled",
    },
)


class GoalSearchRequest(BaseTrackerEntity):
    """Body of `POST /v3/entities/goal/_search`.

    The endpoint accepts a free-form filter object plus an optional sort spec.
    Pass-through `extra="allow"` keeps the wrapper forward-compatible with
    additional filter fields that the API may add later.
    """

    model_config = ConfigDict(extra="allow")

    input: str | None = Field(default=None, description="Free-text search query")
    filter: dict[str, Any] | None = Field(default=None, description="Filter object")
    orderBy: str | None = NoneExcludedField
    orderAsc: bool | None = NoneExcludedField
    rootOnly: bool | None = NoneExcludedField
