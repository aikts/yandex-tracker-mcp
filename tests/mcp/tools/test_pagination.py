from unittest.mock import AsyncMock

import pytest

from mcp_tracker.mcp.tools._pagination import iter_pages


async def collect(fetch: AsyncMock, page: int | None, per_page: int) -> list[list[int]]:
    return [batch async for batch in iter_pages(fetch, page=page, per_page=per_page)]


class TestIterPages:
    async def test_walks_until_a_short_page(self) -> None:
        """A page shorter than per_page is the last one, so the walk must not
        spend a request on the empty page past the end of the data."""
        fetch = AsyncMock(side_effect=[[1, 2], [3, 4], [5]])

        pages = await collect(fetch, page=None, per_page=2)

        assert pages == [[1, 2], [3, 4], [5]]
        assert [call.args[0] for call in fetch.call_args_list] == [1, 2, 3]

    async def test_walks_until_an_empty_page(self) -> None:
        """A listing whose size is a multiple of per_page only ends on an empty
        page."""
        fetch = AsyncMock(side_effect=[[1, 2], [3, 4], []])

        pages = await collect(fetch, page=None, per_page=2)

        assert pages == [[1, 2], [3, 4]]
        assert [call.args[0] for call in fetch.call_args_list] == [1, 2, 3]

    async def test_yields_nothing_when_first_page_is_empty(self) -> None:
        fetch = AsyncMock(side_effect=[[]])

        assert await collect(fetch, page=None, per_page=50) == []
        fetch.assert_called_once_with(1)

    @pytest.mark.parametrize("page", [1, 3])
    async def test_returns_the_requested_page_alone(self, page: int) -> None:
        fetch = AsyncMock(side_effect=[[1, 2]])

        pages = await collect(fetch, page=page, per_page=2)

        assert pages == [[1, 2]]
        fetch.assert_called_once_with(page)
