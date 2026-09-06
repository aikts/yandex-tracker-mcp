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
        original.component_get.return_value = Component.model_construct(
            id=856, version=1, name="Design"
        )
        original.component_create.return_value = Component.model_construct(
            id=857, version=1, name="Backend"
        )
        original.component_update.return_value = Component.model_construct(
            id=856, version=2, name="Design"
        )
        original.component_delete.return_value = None
        return original

    @pytest.fixture
    def caching_components_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.components(mock_original)

    async def test_component_get_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_components_protocol.component_get(856, auth=yandex_auth)

        mock_original.component_get.assert_called_once_with(856, auth=yandex_auth)
        assert result == mock_original.component_get.return_value

    async def test_component_get_calls_original_without_auth(
        self, caching_components_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_components_protocol.component_get(856)

        mock_original.component_get.assert_called_once_with(856, auth=None)
        assert result == mock_original.component_get.return_value

    async def test_component_get_is_not_cached(
        self, caching_components_protocol: Any, mock_original: AsyncMock
    ) -> None:
        await caching_components_protocol.component_get(856)
        await caching_components_protocol.component_get(856)

        assert mock_original.component_get.call_count == 2

    async def test_component_create_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_components_protocol.component_create(
            "AP",
            name="Backend",
            description="Server side",
            lead="i.ivanov",
            assign_auto=True,
            auth=yandex_auth,
        )

        mock_original.component_create.assert_called_once_with(
            "AP",
            name="Backend",
            description="Server side",
            lead="i.ivanov",
            assign_auto=True,
            auth=yandex_auth,
        )
        assert result == mock_original.component_create.return_value

    async def test_component_create_calls_original_without_auth(
        self, caching_components_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_components_protocol.component_create(
            "AP", name="Backend"
        )

        mock_original.component_create.assert_called_once_with(
            "AP",
            name="Backend",
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
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_components_protocol.component_update(
            856,
            version=1,
            name="Design",
            description="Design work",
            lead="i.ivanov",
            assign_auto=False,
            auth=yandex_auth,
        )

        mock_original.component_update.assert_called_once_with(
            856,
            version=1,
            name="Design",
            description="Design work",
            lead="i.ivanov",
            assign_auto=False,
            clear_lead=False,
            auth=yandex_auth,
        )
        assert result == mock_original.component_update.return_value

    async def test_component_update_forwards_clear_lead(
        self, caching_components_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_components_protocol.component_update(
            856, version=1, clear_lead=True
        )

        mock_original.component_update.assert_called_once_with(
            856,
            version=1,
            name=None,
            description=None,
            lead=None,
            assign_auto=None,
            clear_lead=True,
            auth=None,
        )
        assert result == mock_original.component_update.return_value

    async def test_component_update_calls_original_without_auth(
        self, caching_components_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_components_protocol.component_update(
            856, version=1, name="Design"
        )

        mock_original.component_update.assert_called_once_with(
            856,
            version=1,
            name="Design",
            description=None,
            lead=None,
            assign_auto=None,
            clear_lead=False,
            auth=None,
        )
        assert result == mock_original.component_update.return_value

    async def test_component_delete_calls_original(
        self,
        caching_components_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_components_protocol.component_delete(
            856, auth=yandex_auth
        )

        mock_original.component_delete.assert_called_once_with(856, auth=yandex_auth)
        assert result is None

    async def test_component_delete_calls_original_without_auth(
        self, caching_components_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_components_protocol.component_delete(856)

        mock_original.component_delete.assert_called_once_with(856, auth=None)
        assert result is None
