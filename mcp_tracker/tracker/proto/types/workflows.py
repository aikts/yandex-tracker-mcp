from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField


class Workflow(BaseTrackerEntity):
    """A Yandex Tracker workflow (used in a queue's issueTypesConfig)."""

    id: str = Field(description="Workflow id (org-specific, e.g. 'W1')")
    name: str | None = NoneExcludedField
