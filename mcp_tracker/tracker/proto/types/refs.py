from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class BaseReference(BaseTrackerEntity):
    id: Any | None = None


class IssueTypeReference(BaseReference):
    key: str | None = None
    display: str | None = None


class PriorityReference(BaseReference):
    key: str | None = None
    display: str | None = None


class QueueReference(BaseReference):
    key: str | None = None
    display: str | None = None


class StatusReference(BaseModel):
    key: str | None = None
    display: str | None = None


class SprintReference(BaseReference):
    display: str | None = None


class BoardReference(BaseReference):
    display: str | None = None


class IssueBoardReference(BaseTrackerEntity):
    """A board an issue shows up on, as nested in an issue record.

    Tracker spells this one differently from its other references: `name`
    instead of `display`, and a numeric id. That id is what `board_get`,
    `board_get_columns` and `board_get_sprints` take.
    """

    id: int | None = Field(
        None,
        description="Board identifier, as taken by the `board_get`, "
        "`board_get_columns` and `board_get_sprints` tools",
    )
    name: str | None = Field(None, description="Board name")


class UserReference(BaseReference):
    display: str | None = None
    cloud_uid: str | None = Field(
        None,
        validation_alias=AliasChoices("cloudUid", "cloud_uid"),
        serialization_alias="cloudUid",
    )
    passport_uid: int | None = Field(
        None,
        validation_alias=AliasChoices("passportUid", "passport_uid"),
        serialization_alias="passportUid",
    )


class IssueReference(BaseReference):
    key: str | None = None
    display: str | None = None


class ComponentReference(BaseReference):
    display: str | None = None
