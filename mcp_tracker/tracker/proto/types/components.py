from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.refs import QueueReference


class Component(BaseTrackerEntity):
    """Component with a queue."""

    id: int | None = NoneExcludedField
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    queue: QueueReference | None = NoneExcludedField
