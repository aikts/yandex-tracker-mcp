"""Pagination helpers shared by the listing tools."""

from collections.abc import AsyncIterator, Awaitable, Callable

from mcp_tracker.tracker.proto.types.pagination import ItemT, PaginatedResult


async def iter_pages(
    fetch: Callable[[int], Awaitable[PaginatedResult[ItemT]]],
    *,
    page: int | None,
    per_page: int,
) -> AsyncIterator[PaginatedResult[ItemT]]:
    """Yield the pages of a paginated Tracker listing.

    ``page`` returns that single page; None walks the listing from the first
    one. A walk stops as soon as the data is exhausted, which is either the
    page count Tracker reports or - when it reports none - a page shorter than
    ``per_page``.
    """
    current_page = 1 if page is None else page

    while True:
        batch = await fetch(current_page)
        if not batch.values:
            return

        yield batch

        if page is not None:
            return
        if batch.pages is not None:
            # Tracker says how many pages there are, so the walk can stop on the
            # last one instead of spending a request on the empty page past it.
            if current_page >= batch.pages:
                return
        elif len(batch.values) < per_page:
            return

        current_page += 1


async def collect_pages(
    fetch: Callable[[int], Awaitable[PaginatedResult[ItemT]]],
    *,
    page: int | None,
    per_page: int,
    visible: Callable[[list[ItemT]], list[ItemT]] | None = None,
    restricted: bool = False,
) -> PaginatedResult[ItemT]:
    """Collect ``page`` alone, or every page, into one result.

    ``visible`` filters each batch down to what the caller may see. Doing so
    makes the totals Tracker reported describe more than ``values`` holds, so
    they are dropped whenever ``restricted`` says a filter is configured - as
    they are on a full walk, which already returned every item there is.
    Keeping that decision here is what stops a new listing tool from reporting
    totals that count the rows it just hid.
    """
    values: list[ItemT] = []
    last_page: PaginatedResult[ItemT] | None = None

    async for batch in iter_pages(fetch, page=page, per_page=per_page):
        last_page = batch
        values.extend(visible(batch.values) if visible else batch.values)

    if last_page is None or restricted or page is None:
        return PaginatedResult[ItemT](values=values)

    return PaginatedResult[ItemT](
        values=values, hits=last_page.hits, pages=last_page.pages
    )
