from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, none_excluder


class Resolution(BaseTrackerEntity):
    id: int = Field(description="Unique resolution identifier")
    key: str = Field(description="Resolution key")
    version: int | None = Field(
        None, description="Resolution version", exclude_if=none_excluder
    )
    name: str | None = Field(
        None, description="Displayed resolution name", exclude_if=none_excluder
    )
    description: str | None = Field(
        default=None, description="Resolution description", exclude_if=none_excluder
    )
    order: int | None = Field(
        None,
        description="Display weight for ordering resolutions",
        exclude_if=none_excluder,
    )
