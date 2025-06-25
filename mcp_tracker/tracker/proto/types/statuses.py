from typing import Literal

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class Status(BaseTrackerEntity):
    version: int = Field(description="Status version")
    key: str = Field(description="Status key")
    name: str = Field(description="Displayed status name")
    description: str | None = Field(default=None, description="Status description")
    order: int = Field(description="Status order")
    type: Literal["new", "inProgress", "paused", "done", "cancelled"] = Field(
        description="Status type"
    )
