"""Guard: an issue must expose the boards it shows up on as a typed field.

Tracker returns `boards` on every issue that any board's filter picks up. The
model used to leave it unmodelled, so `extra="allow"` leaked it into the answer
while the tool's `outputSchema` never mentioned it and `fields` could not
select it.
"""

from typing import Any

import pytest

from mcp_tracker.tracker.proto.types.issues import (
    ISSUE_FIELD_API_NAMES,
    Issue,
    resolve_issue_field,
)
from mcp_tracker.tracker.proto.types.refs import IssueBoardReference


@pytest.fixture
def issue_payload() -> dict[str, Any]:
    """An issue as `/v3/issues/_search` returns it, boards and sprint included."""
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/LEVELARM-1169",
        "id": "5f0000000000000000000001",
        "key": "LEVELARM-1169",
        "version": 12,
        "summary": "Что-то сломалось",
        "boards": [{"id": 2, "name": "Доска проекта Level ARM"}],
        "sprint": [
            {
                "self": "https://api.tracker.yandex.net/v3/sprints/1241",
                "id": "1241",
                "display": "Спринт 54",
            }
        ],
    }


class TestIssueBoards:
    def test_boards_are_typed(self, issue_payload: dict[str, Any]) -> None:
        issue = Issue.model_validate(issue_payload)

        assert issue.boards is not None
        assert len(issue.boards) == 1
        board = issue.boards[0]
        assert isinstance(board, IssueBoardReference)
        assert board.id == 2
        assert board.name == "Доска проекта Level ARM"

    def test_board_id_is_an_int_the_board_tools_accept(
        self, issue_payload: dict[str, Any]
    ) -> None:
        """`board_get` / `board_get_sprints` take an int, so the id has to be one."""
        issue = Issue.model_validate(issue_payload)

        assert issue.boards is not None
        assert isinstance(issue.boards[0].id, int)

    def test_boards_are_declared_in_the_schema(self) -> None:
        assert "boards" in Issue.model_json_schema()["properties"]

    def test_boards_can_be_selected_with_fields(self) -> None:
        # `fields` is free-form, so the guard is that `boards` resolves as a
        # declared field: asked for by name it goes to the API as `boards` and
        # comes back on the typed attribute rather than in the model's extras.
        assert "boards" in ISSUE_FIELD_API_NAMES
        assert resolve_issue_field("boards") == ("boards", "boards")

    def test_boards_round_trip_under_the_tracker_name(
        self, issue_payload: dict[str, Any]
    ) -> None:
        issue = Issue.model_validate(issue_payload)

        dumped = issue.model_dump(mode="json", by_alias=True)

        assert dumped["boards"] == [{"id": 2, "name": "Доска проекта Level ARM"}]

    def test_an_issue_on_no_board_omits_the_field(self) -> None:
        issue = Issue.model_validate({"key": "TEST-1", "summary": "Без доски"})

        assert issue.boards is None
        assert "boards" not in issue.model_dump(mode="json", by_alias=True)

    def test_sprint_reference_survives_a_string_id(
        self, issue_payload: dict[str, Any]
    ) -> None:
        """Tracker returns the sprint id as a string here but as an int elsewhere."""
        issue = Issue.model_validate(issue_payload)

        assert issue.sprint is not None
        assert issue.sprint[0].id == "1241"
        assert issue.sprint[0].display == "Спринт 54"
