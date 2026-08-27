import datetime
from enum import Enum

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import (
    BaseTrackerEntity,
    NoneExcludedField,
    none_excluder,
)
from mcp_tracker.tracker.proto.types.refs import (
    BaseReference,
    BoardReference,
    UserReference,
)
from mcp_tracker.tracker.proto.types.statuses import Status


class BoardColumn(BaseReference):
    """A column of an agile board, as nested in a board record."""

    display: str | None = None


class BoardColumnStatus(BaseReference):
    """An issue status that lands in a board column."""

    key: str | None = Field(
        None, exclude_if=none_excluder, description="Status key, e.g. 'inProgress'"
    )
    display: str | None = Field(
        None, exclude_if=none_excluder, description="Displayed status name"
    )


class BoardColumnDetail(BaseTrackerEntity):
    """A column of an agile board with the statuses mapped onto it.

    `GET /v3/boards/{id}/columns` answers with more than the columns nested in
    a board record: it says which issue statuses land in which column, and it
    spells the column out as `id` (a number) / `name` rather than the nested
    form's `id` (a string) / `display`.
    """

    id: int | None = Field(
        None, exclude_if=none_excluder, description="Column identifier"
    )
    name: str | None = NoneExcludedField
    statuses: list[BoardColumnStatus] | None = Field(
        None,
        exclude_if=none_excluder,
        description="Issue statuses shown in this column",
    )


class BoardFilterValueRef(BaseReference):
    """A value referenced by a board filter: a queue, an issue type, a user, ..."""

    key: str | None = Field(
        None, exclude_if=none_excluder, description="Key of the referenced entity"
    )
    display: str | None = Field(
        None, exclude_if=none_excluder, description="Human-readable name"
    )


class BoardFilterFieldValue(BaseTrackerEntity):
    """One value a board's auto-filter matches on.

    A condition is either a concrete value (`fixed`) or a macro (`macro`), so a
    board that collects "issues with no resolution" carries `empty()` here and
    no `fixed` at all. `fixed` is a reference object for most fields but a bare
    string for the enumerated ones such as `statusType`.
    """

    fixed: BoardFilterValueRef | str | None = Field(
        None,
        exclude_if=none_excluder,
        description="The matched value, e.g. a queue or an issue type",
    )
    macro: str | None = Field(
        None,
        exclude_if=none_excluder,
        description="Condition applied instead of a fixed value: "
        "'empty()' or 'notEmpty()'",
    )
    invert: bool | None = Field(
        None,
        exclude_if=none_excluder,
        description="True when the condition is negated ('is not')",
    )


class BoardFilterField(BaseTrackerEntity):
    """A field a board's auto-filter matches on, with the values it accepts."""

    id: str | None = NoneExcludedField
    key: str | None = NoneExcludedField
    name: str | None = NoneExcludedField
    display: str | None = NoneExcludedField
    fieldType: str | None = NoneExcludedField
    value: list[BoardFilterFieldValue] | None = Field(
        None, exclude_if=none_excluder, description="Accepted values of this field"
    )


class BoardLiveFilter(BaseTrackerEntity):
    """The field conditions of a board's auto-filter.

    Tracker repeats the same fields under `filterFieldsOrder` to record their
    display order; that is a UI detail and `extra="ignore"` drops it, together
    with the field metadata (`schema`, `qlFieldType`, `fullLocalization`, ...)
    that `queue_get_fields` already describes.
    """

    fieldValues: list[BoardFilterField] | None = Field(
        None, exclude_if=none_excluder, description="Conditions an issue has to match"
    )


class BoardFilterSettings(BaseTrackerEntity):
    """One half of a board's auto-filter: what puts issues on it, or takes them off."""

    liveFilter: BoardLiveFilter | None = NoneExcludedField
    statuses: list[Status] | None = Field(
        None,
        exclude_if=none_excluder,
        description="Issue statuses this rule applies to",
    )
    checkResolutionPresence: bool | None = NoneExcludedField
    maxTimeInToRemoveState: str | None = Field(
        None,
        exclude_if=none_excluder,
        description="How long an issue stays before the rule fires, as an ISO-8601 "
        "duration (e.g. 'P2W' for two weeks)",
    )
    enabled: bool | None = NoneExcludedField


class BoardAutoFilterSettings(BaseTrackerEntity):
    """Which issues a board picks up automatically, and which it drops.

    This is the closest thing a board has to a query: `addFilterSettings`
    describes what lands on the board (usually a queue, sometimes narrowed by
    issue type or status), `removeFilterSettings` what leaves it.
    """

    addFilterSettings: BoardFilterSettings | None = NoneExcludedField
    removeFilterSettings: BoardFilterSettings | None = NoneExcludedField
    addActionSettings: BoardFilterSettings | None = NoneExcludedField
    removeActionSettings: BoardFilterSettings | None = NoneExcludedField


class Board(BaseTrackerEntity):
    """An agile board ("доска задач") of the organization."""

    # `fields` projection nulls out what the caller did not ask for, so an id
    # that stays required would leave `"id": null` against a schema saying int.
    id: int | None = Field(
        None, exclude_if=none_excluder, description="Board identifier"
    )
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    createdAt: datetime.datetime | None = NoneExcludedField
    updatedAt: datetime.datetime | None = NoneExcludedField
    createdBy: UserReference | None = NoneExcludedField
    columns: list[BoardColumn] | None = NoneExcludedField
    autoFilterSettings: BoardAutoFilterSettings | None = Field(
        None,
        exclude_if=none_excluder,
        description="Which issues the board picks up automatically. This is the "
        "board's filter - read it to learn which queue the board is about.",
    )
    estimateBy: BoardFilterValueRef | None = Field(
        None,
        exclude_if=none_excluder,
        description="Field the board estimates issues by, e.g. 'storyPoints'",
    )
    useRanking: bool | None = Field(
        None,
        exclude_if=none_excluder,
        description="Whether issues are ordered by manual ranking",
    )
    country: BoardFilterValueRef | None = Field(
        None,
        exclude_if=none_excluder,
        description="Country whose working calendar the board uses",
    )
    calendar: BaseReference | None = Field(
        None,
        exclude_if=none_excluder,
        description="Working calendar used to count working days in a sprint",
    )


class Sprint(BaseTrackerEntity):
    """A sprint of an agile board."""

    id: int | None = Field(
        None, exclude_if=none_excluder, description="Sprint identifier"
    )
    version: int | None = NoneExcludedField
    name: str | None = NoneExcludedField
    board: BoardReference | None = Field(
        None,
        exclude_if=none_excluder,
        description="The board this sprint belongs to. Tracker sends its `id` as a "
        "string here, while `board_get`, `board_get_columns` and `board_get_sprints` "
        "take a number - pass it as an integer.",
    )
    status: str | None = Field(
        None,
        exclude_if=none_excluder,
        description="Sprint status: 'draft' (open), 'in_progress' (the currently "
        "running sprint), 'released' (finished) or 'archived'",
    )
    archived: bool | None = NoneExcludedField
    createdAt: datetime.datetime | None = NoneExcludedField
    createdBy: UserReference | None = NoneExcludedField
    startDate: datetime.date | None = Field(
        None, exclude_if=none_excluder, description="Planned sprint start date"
    )
    endDate: datetime.date | None = Field(
        None, exclude_if=none_excluder, description="Planned sprint end date"
    )
    startDateTime: datetime.datetime | None = Field(
        None, exclude_if=none_excluder, description="Actual sprint start date and time"
    )
    endDateTime: datetime.datetime | None = Field(
        None, exclude_if=none_excluder, description="Actual sprint end date and time"
    )


class BoardsPage(BaseTrackerEntity):
    """A page of boards plus the cursor to fetch the next one.

    `GET /v3/boards/_paginate` walks the listing by board id rather than by page
    number, so this follows the cursor convention the changelog and comment
    tools use: pass `next_cursor` back as `cursor` until it comes back null.
    """

    boards: list[Board]
    next_cursor: int | None = Field(
        None,
        description="Id of the last board on this page, to be passed back as "
        "`cursor` for the next one. Null when this was the last page.",
    )


BoardFieldsEnum = Enum(  # type: ignore[misc]
    "BoardFieldsEnum",
    {key: key for key in Board.model_fields.keys()},
)

SprintFieldsEnum = Enum(  # type: ignore[misc]
    "SprintFieldsEnum",
    {key: key for key in Sprint.model_fields.keys()},
)
