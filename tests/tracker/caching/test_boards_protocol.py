from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import Board, BoardColumnDetail, Sprint


class TestCachingBoardsProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.boards_list.return_value = [Board(id=1, name="My board")]
        original.board_get_sprints.return_value = [
            Sprint(id=44, name="Sprint 1", status="in_progress")
        ]
        original.board_get.return_value = Board(id=1, name="My board")
        original.board_get_columns.return_value = [
            BoardColumnDetail(id=1, name="Открыт")
        ]
        return original

    @pytest.fixture
    def caching_boards_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.boards(mock_original)

    async def test_boards_list_calls_original(
        self,
        caching_boards_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_boards_protocol.boards_list(
            per_page=25, cursor=18, auth=yandex_auth
        )

        mock_original.boards_list.assert_called_once_with(
            per_page=25, cursor=18, auth=yandex_auth
        )
        assert result == mock_original.boards_list.return_value

    async def test_boards_list_calls_original_without_auth(
        self, caching_boards_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards_protocol.boards_list()

        mock_original.boards_list.assert_called_once_with(
            per_page=100, cursor=None, auth=None
        )
        assert result == mock_original.boards_list.return_value

    async def test_board_get_sprints_calls_original(
        self,
        caching_boards_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_boards_protocol.board_get_sprints(3, auth=yandex_auth)

        mock_original.board_get_sprints.assert_called_once_with(3, auth=yandex_auth)
        assert result == mock_original.board_get_sprints.return_value

    async def test_board_get_sprints_calls_original_without_auth(
        self, caching_boards_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards_protocol.board_get_sprints(3)

        mock_original.board_get_sprints.assert_called_once_with(3, auth=None)
        assert result == mock_original.board_get_sprints.return_value

    async def test_board_get_calls_original(
        self,
        caching_boards_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_boards_protocol.board_get(1, auth=yandex_auth)

        mock_original.board_get.assert_called_once_with(1, auth=yandex_auth)
        assert result == mock_original.board_get.return_value

    async def test_board_get_calls_original_without_auth(
        self, caching_boards_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards_protocol.board_get(1)

        mock_original.board_get.assert_called_once_with(1, auth=None)
        assert result == mock_original.board_get.return_value

    async def test_board_get_columns_calls_original(
        self,
        caching_boards_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_boards_protocol.board_get_columns(1, auth=yandex_auth)

        mock_original.board_get_columns.assert_called_once_with(1, auth=yandex_auth)
        assert result == mock_original.board_get_columns.return_value

    async def test_board_get_columns_calls_original_without_auth(
        self, caching_boards_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_boards_protocol.board_get_columns(1)

        mock_original.board_get_columns.assert_called_once_with(1, auth=None)
        assert result == mock_original.board_get_columns.return_value
