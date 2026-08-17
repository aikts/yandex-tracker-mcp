"""Input models for issue create/update calls.

How Yandex Tracker resolves a bare scalar depends on the field: `type`,
`priority` and `followers` accept an id, a key or a login, while `components`
read a bare string as a component *name*, so `"694"` looks for a component
named "694" and answers 422. These models exist so callers state which one they
mean, and so `issue_create` and `issue_update` serialize the same values
identically.

When both `id` and `key` are given, Tracker resolves by `id` and ignores the
`key`, which makes it safe to pass a reference copied straight out of an issue.
"""

from typing import Self

from pydantic import BaseModel, Field, model_validator


class IssueParentRef(BaseModel):
    """Parent issue reference."""

    id: str | None = Field(None, description="Parent issue ID")
    key: str | None = Field(None, description="Parent issue key (e.g., 'QUEUE-123')")

    @model_validator(mode="after")
    def _require_a_reference(self) -> Self:
        if self.id is None and self.key is None:
            raise ValueError(
                "parent issue reference requires 'id' or 'key' - an empty object "
                "gives Tracker nothing to resolve"
            )
        return self


class IssueSprintRef(BaseModel):
    """Sprint reference."""

    id: int = Field(..., description="Sprint ID")


class IssueTypeRef(BaseModel):
    """Issue type reference."""

    id: str | None = Field(None, description="Issue type ID")
    key: str | None = Field(None, description="Issue type key (e.g., 'bug', 'task')")

    @model_validator(mode="after")
    def _require_a_reference(self) -> Self:
        if self.id is None and self.key is None:
            raise ValueError(
                "issue type reference requires 'id' or 'key' - an empty object "
                "gives Tracker nothing to resolve"
            )
        return self


class IssuePriorityRef(BaseModel):
    """Priority reference."""

    id: str | None = Field(None, description="Priority ID")
    key: str | None = Field(
        None, description="Priority key (e.g., 'critical', 'normal')"
    )

    @model_validator(mode="after")
    def _require_a_reference(self) -> Self:
        if self.id is None and self.key is None:
            raise ValueError(
                "priority reference requires 'id' or 'key' - an empty object "
                "gives Tracker nothing to resolve"
            )
        return self


class IssueFollowerRef(BaseModel):
    """Follower reference."""

    id: str | int = Field(
        ...,
        description="User ID (uid, e.g. 8000000000000034) or login (e.g. 'jdoe')",
    )


class IssueComponentRef(BaseModel):
    """Queue component reference.

    Exactly one of `id` / `name` must be set: Tracker treats numbers as
    component ids and strings as component names, so `"694"` is a *name*.
    """

    id: int | None = Field(
        None,
        description="Component ID (numeric, as returned by queue_get_metadata "
        "with expand=['components']). A numeric string is accepted and sent as a number.",
    )
    name: str | None = Field(
        None, description="Component name, used only when the ID is unknown"
    )

    @model_validator(mode="after")
    def check_id_or_name(self) -> Self:
        if (self.id is None) == (self.name is None):
            raise ValueError(
                "component reference requires exactly one of 'id' (numeric component ID) "
                "or 'name' (component name)"
            )
        return self

    def to_api_value(self) -> int | str:
        """Render as the scalar Tracker expects inside the `components` array."""
        return self.id if self.id is not None else str(self.name)


class IssueProjectRef(BaseModel):
    """Project configuration for an issue."""

    primary: int | None = Field(
        None, description="Primary project ID (shortId of the project)"
    )
    secondary: list[int] | None = Field(
        None, description="Secondary project IDs (shortId of additional projects)"
    )
