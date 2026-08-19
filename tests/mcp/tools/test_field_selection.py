"""Guard: a `fields` selector must actually shrink the payload.

`set_non_needed_fields_null` blanks what was not asked for, so a model reachable
from a selector only drops the field if it also declares `exclude_if`. Without
that, the "unwanted" fields come back as explicit nulls and the parameter that
exists to save context window silently does nothing.
"""

import datetime
import inspect
from enum import EnumMeta
from typing import Any, get_args

import pytest
from pydantic import BaseModel

from mcp_tracker.mcp.utils import set_non_needed_fields_null
from mcp_tracker.tracker.proto.types.entities import (
    GoalFields,
    GoalFieldsEnum,
    PortfolioFields,
    PortfolioFieldsEnum,
    ProjectFields,
    ProjectFieldsEnum,
)
from mcp_tracker.tracker.proto.types.issues import (
    AttachmentFieldsEnum,
    CommentFieldsEnum,
    Issue,
    IssueAttachment,
    IssueComment,
    Worklog,
    WorklogFieldsEnum,
)
from mcp_tracker.tracker.proto.types.queues import Queue, QueueFieldsEnum
from mcp_tracker.tracker.proto.types.users import User, UserFieldsEnum

# Every model an MCP tool exposes a field selector over. `Issue` has no enum of
# its own any more - `issues_find` takes free-form names - but it is filtered by
# the same helper, so it is held to the same rule.
SELECTABLE_MODELS: list[tuple[type[BaseModel], EnumMeta | None]] = [
    (Issue, None),
    (Queue, QueueFieldsEnum),
    (User, UserFieldsEnum),
    (IssueComment, CommentFieldsEnum),
    (Worklog, WorklogFieldsEnum),
    (IssueAttachment, AttachmentFieldsEnum),
    (ProjectFields, ProjectFieldsEnum),
    (PortfolioFields, PortfolioFieldsEnum),
    (GoalFields, GoalFieldsEnum),
]

IDS = [model.__name__ for model, _ in SELECTABLE_MODELS]


@pytest.mark.parametrize(("model", "enum"), SELECTABLE_MODELS, ids=IDS)
class TestSelectableModels:
    def test_nullable_fields_are_dropped_when_null(
        self, model: type[BaseModel], enum: EnumMeta | None
    ) -> None:
        offenders = [
            name
            for name, field in model.model_fields.items()
            if type(None) in get_args(field.annotation)
            and getattr(field, "exclude_if", None) is None
        ]

        assert not offenders, (
            f"{model.__name__} is reachable from a `fields` selector, so these "
            f"optional fields need `exclude_if=none_excluder` (use "
            f"`NoneExcludedField`) or they come back as explicit nulls: {offenders}"
        )

    def test_filtering_leaves_only_what_was_asked_for(
        self, model: type[BaseModel], enum: EnumMeta | None
    ) -> None:
        """The end-to-end promise, checked on a fully-populated instance."""
        required = {
            name for name, field in model.model_fields.items() if field.is_required()
        }
        payload: dict[str, Any] = {
            name: _sample(model.model_fields[name].annotation) for name in required
        }
        keep = next(
            name
            for name, field in model.model_fields.items()
            if type(None) in get_args(field.annotation)
        )
        payload[keep] = _sample(model.model_fields[keep].annotation)

        item = model.model_validate(payload)
        set_non_needed_fields_null([item], {keep})

        # Required fields cannot be nulled without violating the output schema,
        # so they stay; nothing else may survive.
        dumped = item.model_dump(by_alias=True)
        allowed = {
            (
                model.model_fields[n].serialization_alias
                or model.model_fields[n].alias
                or n
            )
            for n in required | {keep}
        }
        assert set(dumped) <= allowed, f"{model.__name__} kept {set(dumped) - allowed}"


def _sample(annotation: Any) -> Any:
    """Smallest value that validates for the field's declared type."""
    args = [a for a in get_args(annotation) if a is not type(None)]
    target = args[0] if args else annotation
    simple: dict[Any, Any] = {
        int: 1,
        float: 1.0,
        bool: True,
        str: "x",
        datetime.datetime: datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        datetime.date: datetime.date(2026, 1, 1),
        datetime.timedelta: datetime.timedelta(hours=1),
    }
    if target in simple:
        return simple[target]
    origin = getattr(target, "__origin__", None)
    if origin is list:
        return []
    if origin is dict:
        return {}
    if inspect.isclass(target) and issubclass(target, BaseModel):
        return {
            name: _sample(field.annotation)
            for name, field in target.model_fields.items()
            if field.is_required()
        }
    return "x"
