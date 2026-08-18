from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class Priority(BaseTrackerEntity):
    id: int = Field(description="Priority ID")
    version: int = Field(description="Priority version")
    key: str = Field(description="Priority key")
    name: str = Field(description="Displayed priority name")
    description: str | None = Field(default=None, description="Priority description")
    order: int = Field(description="Priority order")
