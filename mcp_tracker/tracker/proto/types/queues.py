from datetime import date
from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.refs import IssueTypeReference, PriorityReference
from mcp_tracker.tracker.proto.types.resolutions import Resolution


class QueueIssueTypeConfig(BaseTrackerEntity):
    """Issue type configuration within a queue, including available resolutions."""

    issueType: IssueTypeReference | None = Field(
        None, description="Issue type reference"
    )
    resolutions: list[Resolution] | None = Field(
        None, description="Available resolutions for this issue type"
    )


class Queue(BaseTrackerEntity):
    model_config = ConfigDict(extra="ignore")

    id: int | None = NoneExcludedField
    key: str | None = NoneExcludedField
    name: str | None = NoneExcludedField
    description: str | None = NoneExcludedField
    defaultType: IssueTypeReference | None = NoneExcludedField
    defaultPriority: PriorityReference | None = NoneExcludedField
    issueTypesConfig: list[QueueIssueTypeConfig] | None = NoneExcludedField


# Expand options for queue_get API
QueueExpandOption = Literal[
    "all",
    "projects",
    "components",
    "versions",
    "types",
    "team",
    "workflows",
    "fields",
    "issueTypesConfig",
]


QueueFieldsEnum = Enum(  # type: ignore[misc]  # ty: ignore[unused-ignore-comment]
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
