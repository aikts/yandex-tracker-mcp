"""Pydantic types for Yandex Tracker entities (projects, portfolios, goals)."""

from typing import Literal

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField

# Entity kinds supported by the Yandex Tracker "entities" API.
EntityType = Literal["project", "portfolio", "goal"]


class Entity(BaseTrackerEntity):
    """A Yandex Tracker entity: a project, portfolio or goal.

    Entities group issues across queues and are managed via the
    ``/v3/entities/<type>`` endpoints. ``id`` is the long opaque identifier used
    for API calls; ``shortId`` is the human-facing number shown in the UI.
    """

    id: str
    version: int | None = NoneExcludedField
    shortId: int | None = NoneExcludedField
    entityType: str | None = NoneExcludedField
