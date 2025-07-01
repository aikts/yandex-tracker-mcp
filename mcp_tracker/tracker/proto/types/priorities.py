from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class Priority(BaseTrackerEntity):
    version: int = Field(description="Priority version")
    key: str = Field(description="Priority key")
    name: str = Field(description="Displayed priority name")
    order: int = Field(description="Priority order")
