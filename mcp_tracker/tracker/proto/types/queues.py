from datetime import date
from enum import Enum

from pydantic import ConfigDict

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.refs import IssueTypeReference, PriorityReference


class Queue(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    id: int | None = NoneExcludedField
    key: str | None = NoneExcludedField
    name: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    defaultType: IssueTypeReference | None = NoneExcludedField
    defaultPriority: PriorityReference | None = NoneExcludedField


QueueFieldsEnum = Enum(  # type: ignore[misc]
    "QueueFieldsEnum",
    {key: key for key in Queue.model_fields.keys()},
)


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
