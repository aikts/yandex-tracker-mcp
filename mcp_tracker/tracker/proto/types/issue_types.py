from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity


class IssueType(BaseTrackerEntity):
    id: int = Field(description="Issue type ID")
    version: int = Field(description="Issue type version")
    key: str = Field(description="Issue type key")
    name: str = Field(description="Displayed issue type name")
    description: str | None = Field(default=None, description="Issue type description")
