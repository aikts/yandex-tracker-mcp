from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.components import Component


class TestCachingComponentsProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.components_list.return_value = [
            Component(id=111175, version=1, name="Test Component")
        ]
        original.component_get.return_value = Component(
            id=111175, version=1, name="Test Component"
        )
        original.component_create.return_value = Component(
            id=111176, version=1, name="New Component"
        )
        original.component_update.return_value = Component(
            id=111175, version=2, name="Updated Component"
        )
        original.component_delete.return_value = None
        return original

    @pytest.fixture
    def caching_components_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.components(mock_original)

    async def test_components_list_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_components_protocol.components_list(
            per_page=10, page=2, auth=yandex_auth
        )

        mock_original.components_list.assert_called_once_with(
            per_page=10, page=2, auth=yandex_auth
        )
        assert result == mock_original.components_list.return_value

    async def test_component_get_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_components_protocol.component_get(
            111175, auth=yandex_auth
        )

        mock_original.component_get.assert_called_once_with(111175, auth=yandex_auth)
        assert result == mock_original.component_get.return_value

    async def test_component_create_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
    ) -> None:
        result = await caching_components_protocol.component_create(
            "TEST", name="New Component"
        )

        mock_original.component_create.assert_called_once_with(
            "TEST",
            name="New Component",
            description=None,
            lead=None,
            assign_auto=None,
            auth=None,
        )
        assert result == mock_original.component_create.return_value

    async def test_component_update_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
    ) -> None:
        result = await caching_components_protocol.component_update(
            111175, name="Updated Component"
        )

        mock_original.component_update.assert_called_once_with(
            111175, name="Updated Component", description=None, lead=None, auth=None
        )
        assert result == mock_original.component_update.return_value

    async def test_component_delete_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
    ) -> None:
        result = await caching_components_protocol.component_delete(111175)

        mock_original.component_delete.assert_called_once_with(111175, auth=None)
        assert result is None
