from datetime import date

from pydantic import ConfigDict

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity
from mcp_tracker.tracker.proto.types.refs import IssueTypeReference, PriorityReference


class Queue(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    id: int
    key: str | None = None
    name: str | None = None
    description: str | None = None
    defaultType: IssueTypeReference | None = None
    defaultPriority: PriorityReference | None = None


class QueueVersion(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    id: int
    version: int
    name: str
    description: str | None = None
    startDate: date | None = None
    dueDate: date | None = None
    released: bool
    archived: bool
