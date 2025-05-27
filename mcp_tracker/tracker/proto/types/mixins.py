import datetime

from pydantic import AliasChoices, Field

from mcp_tracker.tracker.proto.types.refs import UserReference


class CreatedUpdatedMixin:
    created_at: datetime.datetime | None = Field(
        None, validation_alias=AliasChoices("createdAt", "created_at")
    )
    updated_at: datetime.datetime | None = Field(
        None, validation_alias=AliasChoices("updatedAt", "updated_at")
    )
    created_by: UserReference | None = Field(
        None, validation_alias=AliasChoices("createdBy", "created_by")
    )
    updated_by: UserReference | None = Field(
        None, validation_alias=AliasChoices("updatedBy", "updated_by")
    )
