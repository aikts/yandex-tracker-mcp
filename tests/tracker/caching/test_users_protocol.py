from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.users import User


class TestCachingUsersProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.users_list.return_value = [
            User(uid=123, login="test_user", display="Test User")
        ]
        original.user_get.return_value = User(
            uid=123, login="test_user", display="Test User"
        )
        original.user_get_current.return_value = User(
            uid=456, login="current_user", display="Current User"
        )
        return original

    @pytest.fixture
    def caching_users_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.users(mock_original)

    async def test_users_list_calls_original(
        self,
        caching_users_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_users_protocol.users_list(
            per_page=25, page=2, auth=yandex_auth
        )

        mock_original.users_list.assert_called_once_with(
            per_page=25, page=2, auth=yandex_auth
        )
        assert result == mock_original.users_list.return_value

    async def test_user_get_calls_original(
        self, caching_users_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_users_protocol.user_get("test_user")

        mock_original.user_get.assert_called_once_with("test_user", auth=None)
        assert result == mock_original.user_get.return_value

    async def test_user_get_current_calls_original(
        self,
        caching_users_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_users_protocol.user_get_current(auth=yandex_auth)

        mock_original.user_get_current.assert_called_once_with(auth=yandex_auth)
        assert result == mock_original.user_get_current.return_value
