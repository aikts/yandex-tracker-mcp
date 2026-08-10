import datetime

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, NoneExcludedField
from mcp_tracker.tracker.proto.types.refs import (
    BaseReference,
    BoardReference,
    UserReference,
)


class BoardColumn(BaseReference):
    """A column of an agile board (usually mapped to an issue status)."""

    display: str | None = None


class Board(BaseTrackerEntity):
    """An agile board ("доска задач") of the organization."""

    id: int = Field(description="Board identifier")
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    createdAt: datetime.datetime | None = NoneExcludedField
    updatedAt: datetime.datetime | None = NoneExcludedField
    createdBy: UserReference | None = NoneExcludedField
    columns: list[BoardColumn] | None = NoneExcludedField


class Sprint(BaseTrackerEntity):
    """A sprint of an agile board."""

    id: int = Field(description="Sprint identifier")
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    board: BoardReference | None = NoneExcludedField
    status: str | None = Field(
        None,
        description="Sprint status: 'draft' (open), 'in_progress' (the currently "
        "running sprint), 'released' (finished) or 'archived'",
    )
    archived: bool | None = NoneExcludedField
    createdAt: datetime.datetime | None = NoneExcludedField
    createdBy: UserReference | None = NoneExcludedField
    startDate: datetime.date | None = Field(
        None, description="Planned sprint start date"
    )
    endDate: datetime.date | None = Field(None, description="Planned sprint end date")
    startDateTime: datetime.datetime | None = Field(
        None, description="Actual sprint start date and time"
    )
    endDateTime: datetime.datetime | None = Field(
        None, description="Actual sprint end date and time"
    )
