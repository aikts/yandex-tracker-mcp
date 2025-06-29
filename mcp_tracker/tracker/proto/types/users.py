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
