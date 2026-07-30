from enum import Enum

from pydantic import ConfigDict, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class User(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    uid: int
    login: str
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    display: str | None = None
    email: str | None = None
    external: bool | None = None
    dismissed: bool | None = None


UserFieldsEnum = Enum(  # type: ignore[misc]
    "UserFieldsEnum",
    {key: key for key in User.model_fields.keys()},
)
