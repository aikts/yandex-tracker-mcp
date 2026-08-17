"""Pagination helper shared by the listing tools."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

ItemT = TypeVar("ItemT")


async def iter_pages(
    fetch: Callable[[int], Awaitable[list[ItemT]]],
    *,
    page: int | None,
    per_page: int,
) -> AsyncIterator[list[ItemT]]:
    """Yield the pages of a paginated Tracker listing.

    ``page`` returns that single page; None walks the listing from the first
    one. A page shorter than ``per_page`` is the last one, so a full walk does
    not spend a request on the empty page past the end of the data.
    """
    current_page = 1 if page is None else page

    while True:
        batch = await fetch(current_page)
        if not batch:
            return

        yield batch

        if page is not None or len(batch) < per_page:
            return

        current_page += 1
