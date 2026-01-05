from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class Resolution(BaseTrackerEntity):
    id: int = Field(description="Unique resolution identifier")
    key: str = Field(description="Resolution key")
    version: int = Field(description="Resolution version")
    name: str = Field(description="Displayed resolution name")
    description: str | None = Field(default=None, description="Resolution description")
    order: int = Field(description="Display weight for ordering resolutions")
