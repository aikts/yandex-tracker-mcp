from datetime import date, datetime

import pytest

from mcp_tracker.tracker.proto.types.entities import (
    EntityReference,
    GoalFields,
    ParentEntityRef,
    PortfolioFields,
    ProjectFields,
)
from mcp_tracker.tracker.proto.types.refs import QueueReference


@pytest.mark.parametrize("fields_model", [ProjectFields, PortfolioFields])
def test_entity_fields_accept_date_and_datetime(
    fields_model: type[ProjectFields] | type[PortfolioFields],
) -> None:
    fields = fields_model.model_validate(
        {
            "start": "2026-01-01",
            "end": "2026-12-31T23:59:59+00:00",
        }
    )

    assert fields.start == date(2026, 1, 1)
    assert fields.end == datetime.fromisoformat("2026-12-31T23:59:59+00:00")

    start_formats = {
        schema.get("format")
        for schema in fields_model.model_json_schema()["properties"]["start"]["anyOf"]
    }
    assert {"date", "date-time"} <= start_formats


def test_goal_fields_accept_deadline_without_start() -> None:
    fields = GoalFields.model_validate({"end": "2026-12-31"})

    assert fields.end == date(2026, 12, 31)
    assert "start" not in GoalFields.model_json_schema()["properties"]


def test_documented_entity_references_and_counts() -> None:
    fields = ProjectFields.model_validate(
        {
            "parentEntity": {
                "primary": {"id": "portfolio-1", "display": "Portfolio"},
                "secondary": [{"id": "portfolio-2", "display": "Other"}],
            },
            "issueQueues": [{"id": "1", "key": "TEST", "display": "Test"}],
            "quarter": ["2026 Q1", "2026 Q4"],
            "linkedGoalsCount": 2,
            "lastCommentUpdatedAt": "2026-07-29T12:30:00.000+0000",
        }
    )

    assert fields.parentEntity == ParentEntityRef(
        primary=EntityReference(id="portfolio-1", display="Portfolio"),
        secondary=[EntityReference(id="portfolio-2", display="Other")],
    )
    assert fields.issueQueues == [QueueReference(id="1", key="TEST", display="Test")]
    assert fields.quarter == ["2026 Q1", "2026 Q4"]
    assert fields.linkedGoalsCount == 2
    assert fields.lastCommentUpdatedAt == datetime.fromisoformat(
        "2026-07-29T12:30:00+00:00"
    )


@pytest.mark.parametrize("fields_model", [ProjectFields, PortfolioFields, GoalFields])
def test_last_comment_updated_at_stays_a_timestamp_at_midnight(
    fields_model: type[ProjectFields] | type[PortfolioFields] | type[GoalFields],
) -> None:
    """A timestamp landing exactly on midnight must not collapse to a bare date."""
    fields = fields_model.model_validate(
        {"lastCommentUpdatedAt": "2026-01-01T00:00:00.000+0000"}
    )

    assert fields.lastCommentUpdatedAt == datetime.fromisoformat(
        "2026-01-01T00:00:00+00:00"
    )
    assert '"2026-01-01T00:00:00Z"' in fields.model_dump_json()
