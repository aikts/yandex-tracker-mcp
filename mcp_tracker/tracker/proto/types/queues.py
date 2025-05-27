from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity
from mcp_tracker.tracker.proto.types.refs import IssueTypeReference, PriorityReference


class Queue(BaseTrackerEntity):
    id: int
    key: str | None = None
    name: str | None = None
    description: str | None = None
    defaultType: IssueTypeReference | None = None
    defaultPriority: PriorityReference | None = None
