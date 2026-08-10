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


def test_goal_key_results_and_metrics_are_parsed() -> None:
    """`keyResultItems` explains a goal's progressPercentage, so it must survive
    parsing rather than being dropped by the model's extra="ignore"."""
    fields = GoalFields.model_validate(
        {
            "progressPercentage": 40.0,
            "keyResultItems": [
                {
                    "id": "kr-1",
                    "text": "Ship the thing",
                    "type": "value",
                    "achieved": False,
                    "progress": {"start": 0, "end": 100, "current": 40},
                    "deadline": {
                        "date": "2026-12-31T00:00:00.000+0000",
                        "deadlineType": "date",
                        "isExceeded": False,
                    },
                    "assignee": {"id": "user123", "display": "Test User"},
                }
            ],
            "metricItems": [
                {"id": "m-1", "text": "Conversion", "url": "https://example.com/w/1"}
            ],
        }
    )

    assert fields.keyResultItems is not None
    key_result = fields.keyResultItems[0]
    assert key_result.type == "value"
    assert key_result.progress is not None
    assert key_result.progress.current == 40
    assert key_result.deadline is not None
    assert key_result.deadline.is_exceeded is False
    assert key_result.assignee is not None
    assert key_result.assignee.display == "Test User"
    assert fields.metricItems is not None
    assert fields.metricItems[0].url == "https://example.com/w/1"


@pytest.mark.parametrize(
    "fields_model,expected",
    [
        (ProjectFields, {"metricItems"}),
        (PortfolioFields, {"metricItems"}),
        (GoalFields, {"metricItems", "keyResultItems"}),
    ],
)
def test_metric_and_key_result_fields_are_selectable(
    fields_model: type[ProjectFields] | type[PortfolioFields] | type[GoalFields],
    expected: set[str],
) -> None:
    """Per the API docs metrics exist on all three types, key results only on goals."""
    assert expected <= set(fields_model.model_fields)
    if fields_model is not GoalFields:
        assert "keyResultItems" not in fields_model.model_fields
