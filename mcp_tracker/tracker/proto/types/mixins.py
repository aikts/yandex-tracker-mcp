import datetime

from pydantic import AliasChoices, Field

from mcp_tracker.tracker.proto.types.base import none_excluder
from mcp_tracker.tracker.proto.types.refs import UserReference


class CreatedUpdatedMixin:
    created_at: datetime.datetime | None = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        exclude_if=none_excluder,
    )
    updated_at: datetime.datetime | None = Field(
        None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        exclude_if=none_excluder,
    )
    created_by: UserReference | None = Field(
        None,
        validation_alias=AliasChoices("createdBy", "created_by"),
        exclude_if=none_excluder,
    )
    updated_by: UserReference | None = Field(
        None,
        validation_alias=AliasChoices("updatedBy", "updated_by"),
        exclude_if=none_excluder,
    )


class CreatedMixin:
    created_at: datetime.datetime | None = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        exclude_if=none_excluder,
    )
    created_by: UserReference | None = Field(
        None,
        validation_alias=AliasChoices("createdBy", "created_by"),
        exclude_if=none_excluder,
    )
