from pydantic import ConfigDict

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class User(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    uid: int
    login: str
    first_name: str | None = None
    last_name: str | None = None
    display: str | None = None
    email: str | None = None
    external: bool | None = None
    dismissed: bool | None = None
