from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField


class Component(BaseTrackerEntity):
    """Component within a queue."""

    id: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
