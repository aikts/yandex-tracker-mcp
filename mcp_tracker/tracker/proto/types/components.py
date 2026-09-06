from pydantic import AliasChoices, Field

from mcp_tracker.tracker.proto.types.base import (
    BaseTrackerEntity,
    NoneExcludedField,
    none_excluder,
)
from mcp_tracker.tracker.proto.types.refs import QueueReference, UserReference


class Component(BaseTrackerEntity):
    """A queue component as the API returns it; `description` and `lead` are
    absent when unset, which the `NoneExcludedField` defaults mirror."""

    id: int
    version: int
    name: str
    description: str | None = NoneExcludedField
    queue: QueueReference | None = NoneExcludedField
    lead: UserReference | None = NoneExcludedField
    assign_auto: bool | None = Field(
        None,
        validation_alias=AliasChoices("assignAuto", "assign_auto"),
        serialization_alias="assignAuto",
        exclude_if=none_excluder,
    )
