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


class UserReference(BaseReference):
    display: str | None = None
    cloud_uid: str | None = Field(
        None, validation_alias=AliasChoices("cloudUid", "cloud_uid")
    )
    passport_uid: int | None = Field(
        None, validation_alias=AliasChoices("passportUid", "passport_uid")
    )


class IssueReference(BaseReference):
    key: str | None = None
    display: str | None = None


class ComponentReference(BaseReference):
    display: str | None = None
