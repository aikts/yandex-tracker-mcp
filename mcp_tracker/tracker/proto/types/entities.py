"""Pydantic types for Yandex Tracker entities (projects, portfolios, goals)."""

from typing import Any, Literal

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.refs import UserReference

# Entity kinds supported by the Yandex Tracker "entities" API.
EntityType = Literal["project", "portfolio", "goal"]


class Entity(BaseTrackerEntity):
    """A Yandex Tracker entity: a project, portfolio or goal.

    Entities group issues across queues and are managed via the
    ``/v3/entities/<type>`` endpoints. ``id`` is the long opaque identifier used
    for API calls; ``shortId`` is the human-facing number shown in the UI. On
    read, ``fields`` carries the entity payload (``summary``, ``description``,
    ``entityStatus``, ...).
    """

    id: str
    version: int | None = NoneExcludedField
    shortId: int | None = NoneExcludedField
    entityType: str | None = NoneExcludedField
    createdBy: UserReference | None = NoneExcludedField
    createdAt: str | None = NoneExcludedField
    updatedAt: str | None = NoneExcludedField
    fields: dict[str, Any] | None = NoneExcludedField


class EntitySearchResult(BaseTrackerEntity):
    """Response of the entity search endpoint (`POST /v3/entities/<type>/_search`)."""

    hits: int | None = NoneExcludedField
    pages: int | None = NoneExcludedField
    values: list[Entity] = Field(default_factory=list)
