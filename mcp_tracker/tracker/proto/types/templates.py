from typing import Any

from pydantic import ConfigDict, Field, field_validator

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity, none_excluder
from mcp_tracker.tracker.proto.types.issues import MaillistReference
from mcp_tracker.tracker.proto.types.refs import QueueReference, UserReference


class BaseTemplate(BaseTrackerEntity):
    """Fields shared by Yandex Tracker issue and comment templates.

    Neither ``/v3/issueTemplates`` nor ``/v3/commentTemplates`` is covered by
    the public API reference, so both field sets follow the official Yandex
    Python client (``yandex_tracker_client``), whose ``IssueTemplates`` and
    ``CommentTemplates`` collections declare ``id``, ``self``, ``version``,
    ``name`` and ``queue`` in common.

    ``extra="allow"`` deliberately overrides the ``BaseTrackerEntity`` default
    of ``extra="ignore"``: since the response contract is not documented, any
    field outside the declared set must still reach the caller instead of being
    silently dropped.
    """

    model_config = ConfigDict(extra="allow")

    # The client declares no type for ``id``; Tracker uses both integer ids
    # (statuses, resolutions, issue types) and string ids (fields), so accept
    # either rather than guessing one and failing validation on the other.
    id: str | int | None = Field(
        None, description="Unique template identifier", exclude_if=none_excluder
    )
    version: int | None = Field(
        None, description="Template version", exclude_if=none_excluder
    )
    name: str | None = Field(
        None, description="Displayed template name", exclude_if=none_excluder
    )
    queue: QueueReference | None = Field(
        None,
        description="Queue the template belongs to, if it is queue-specific",
        exclude_if=none_excluder,
    )
    description: str | None = Field(
        None,
        description="What the template itself is for. Not the issue body: an issue "
        "template prefills that through `fieldTemplates.description`",
        exclude_if=none_excluder,
    )

    @field_validator("description", mode="after")
    @classmethod
    def _empty_description_is_no_description(cls, value: str | None) -> str | None:
        """Tracker sends "" for some templates and omits the key for others."""
        return value or None


class IssueTemplate(BaseTemplate):
    """Issue template configured in Yandex Tracker settings.

    Adds ``fieldTemplates`` to the shared fields, per the official client's
    ``IssueTemplates`` collection.
    """

    fieldTemplates: dict[str, Any] | None = Field(
        None,
        description="Issue field values prefilled by the template, keyed by field id",
        exclude_if=none_excluder,
    )


class CommentTemplate(BaseTemplate):
    """Comment template configured in Yandex Tracker settings.

    Adds ``template``, ``summonees`` and ``maillistSummonees``
    to the shared fields, per the official client's ``CommentTemplates``
    collection. The summonee shapes reuse the references already used by
    ``IssueComment`` for the same two fields.
    """

    template: str | None = Field(
        None,
        description="Comment text inserted by the template",
        exclude_if=none_excluder,
    )
    summonees: list[UserReference] | None = Field(
        None,
        description="Users summoned by a comment created from the template",
        exclude_if=none_excluder,
    )
    maillistSummonees: list[MaillistReference] | None = Field(
        None,
        description="Mailing lists summoned by a comment created from the template",
        exclude_if=none_excluder,
    )
