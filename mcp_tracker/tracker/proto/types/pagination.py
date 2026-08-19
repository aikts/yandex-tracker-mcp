from typing import Generic, TypeVar

from pydantic import Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity

ItemT = TypeVar("ItemT")


class PaginatedResult(BaseTrackerEntity, Generic[ItemT]):
    """One page of a listing, plus how much there is in total."""

    values: list[ItemT] = Field(default_factory=list)
    hits: int | None = Field(
        None,
        description="Total items matching the request, across all pages. Null if "
        "unknown or filtered - then page on until a page comes back empty.",
    )
    pages: int | None = Field(
        None,
        description="Total pages at the requested `per_page`; this is the last page "
        "when it equals `page`. Null together with `hits`.",
    )
