from unittest.mock import AsyncMock

import pytest

from mcp_tracker.mcp.tools._pagination import collect_pages, iter_pages
from mcp_tracker.tracker.proto.types.pagination import PaginatedResult
from tests.mcp.conftest import page as make_page


async def collect(fetch: AsyncMock, page: int | None, per_page: int) -> list[list[int]]:
    return [
        batch.values async for batch in iter_pages(fetch, page=page, per_page=per_page)
    ]


class TestIterPages:
    async def test_walks_until_a_short_page(self) -> None:
        """A page shorter than per_page is the last one, so the walk must not
        spend a request on the empty page past the end of the data."""
        fetch = AsyncMock(
            side_effect=[make_page([1, 2]), make_page([3, 4]), make_page([5])]
        )

        pages = await collect(fetch, page=None, per_page=2)

        assert pages == [[1, 2], [3, 4], [5]]
        assert [call.args[0] for call in fetch.call_args_list] == [1, 2, 3]

    async def test_walks_until_an_empty_page(self) -> None:
        """A listing whose size is a multiple of per_page only ends on an empty
        page."""
        fetch = AsyncMock(
            side_effect=[make_page([1, 2]), make_page([3, 4]), make_page([])]
        )

        pages = await collect(fetch, page=None, per_page=2)

        assert pages == [[1, 2], [3, 4]]
        assert [call.args[0] for call in fetch.call_args_list] == [1, 2, 3]

    async def test_yields_nothing_when_first_page_is_empty(self) -> None:
        fetch = AsyncMock(side_effect=[make_page([])])

        assert await collect(fetch, page=None, per_page=50) == []
        fetch.assert_called_once_with(1)

    @pytest.mark.parametrize("page", [1, 3])
    async def test_returns_the_requested_page_alone(self, page: int) -> None:
        fetch = AsyncMock(side_effect=[make_page([1, 2])])

        pages = await collect(fetch, page=page, per_page=2)

        assert pages == [[1, 2]]
        fetch.assert_called_once_with(page)

    async def test_stops_on_the_last_page_tracker_reports(self) -> None:
        """With a page count in hand the walk must not spend a request on the
        empty page past the end, which is what a size that is an exact multiple
        of per_page used to cost."""
        fetch = AsyncMock(
            side_effect=[make_page([1, 2], pages=2), make_page([3, 4], pages=2)]
        )

        pages = await collect(fetch, page=None, per_page=2)

        assert pages == [[1, 2], [3, 4]]
        assert [call.args[0] for call in fetch.call_args_list] == [1, 2]

    async def test_falls_back_to_probing_without_a_page_count(self) -> None:
        fetch = AsyncMock(
            side_effect=[make_page([1, 2]), make_page([3, 4]), make_page([])]
        )

        pages = await collect(fetch, page=None, per_page=2)

        assert pages == [[1, 2], [3, 4]]
        assert [call.args[0] for call in fetch.call_args_list] == [1, 2, 3]

    async def test_yields_the_reported_totals(self) -> None:
        fetch = AsyncMock(side_effect=[make_page([1], hits=403, pages=403)])

        pages = [batch async for batch in iter_pages(fetch, page=1, per_page=1)]

        assert (pages[0].hits, pages[0].pages) == (403, 403)


class TestCollectPages:
    async def test_reports_totals_for_a_single_unrestricted_page(self) -> None:
        fetch = AsyncMock(side_effect=[make_page([1, 2], hits=403, pages=202)])

        result = await collect_pages(fetch, page=2, per_page=2)

        assert result.values == [1, 2]
        assert (result.hits, result.pages) == (403, 202)

    async def test_drops_totals_on_a_full_walk(self) -> None:
        """The walk already returned every item, so a total adds nothing."""
        fetch = AsyncMock(side_effect=[make_page([1], hits=1, pages=1)])

        result = await collect_pages(fetch, page=None, per_page=2)

        assert result.values == [1]
        assert (result.hits, result.pages) == (None, None)

    async def test_drops_totals_when_a_filter_is_configured(self) -> None:
        """Tracker counted rows this server then hid, so its total would overstate."""
        fetch = AsyncMock(side_effect=[make_page([1, 2], hits=403, pages=202)])

        result = await collect_pages(
            fetch,
            page=2,
            per_page=2,
            visible=lambda values: [v for v in values if v != 2],
            restricted=True,
        )

        assert result.values == [1]
        assert (result.hits, result.pages) == (None, None)

    async def test_filters_every_page_of_a_walk(self) -> None:
        fetch = AsyncMock(
            side_effect=[make_page([1, 2], pages=2), make_page([3, 4], pages=2)]
        )

        result = await collect_pages(
            fetch,
            page=None,
            per_page=2,
            visible=lambda values: [v for v in values if v % 2],
        )

        assert result.values == [1, 3]

    async def test_empty_listing_has_no_totals(self) -> None:
        fetch = AsyncMock(side_effect=[make_page([])])

        result = await collect_pages(fetch, page=1, per_page=2)

        assert result.values == []
        assert (result.hits, result.pages) == (None, None)


class TestPaginatedResultSchema:
    async def test_totals_document_when_they_are_null(self) -> None:
        """Parametrizing a generic model drops its docstring from the schema, so
        the caveat has to live on the fields to reach the client at all."""
        properties = PaginatedResult[int].model_json_schema()["properties"]

        for field in ("hits", "pages"):
            assert "Null" in properties[field]["description"], field
