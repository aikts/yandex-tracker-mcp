from enum import Enum

from pydantic import ConfigDict, Field

from mcp_tracker.tracker.proto.types.base import (
    BaseTrackerEntity,
    NoneExcludedField,
    none_excluder,
)


class User(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    uid: int
    login: str
    first_name: str | None = Field(None, alias="firstName", exclude_if=none_excluder)
    last_name: str | None = Field(None, alias="lastName", exclude_if=none_excluder)
    display: str | None = NoneExcludedField
    email: str | None = NoneExcludedField
    external: bool | None = NoneExcludedField
    dismissed: bool | None = NoneExcludedField


UserFieldsEnum = Enum(  # type: ignore[misc]
    "UserFieldsEnum",
    {key: key for key in User.model_fields.keys()},
)
