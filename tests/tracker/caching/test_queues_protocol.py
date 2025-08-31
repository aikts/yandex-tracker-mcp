from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion


class TestCachingQueuesProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.queues_list.return_value = [Queue(id=1, key="TEST", name="Test Queue")]
        original.queues_get_local_fields.return_value = [
            LocalField(id="test-field", key="test", name="Test Field")
        ]
        original.queues_get_tags.return_value = ["tag1", "tag2"]
        original.queues_get_versions.return_value = [
            QueueVersion(id=1, version=1, name="1.0", released=False, archived=False)
        ]
        original.queues_get_fields.return_value = [
            GlobalField(id="field-1", key="status", name="Status")
        ]
        original.queue_get.return_value = Queue(id=1, key="TEST", name="Test Queue")
        return original

    @pytest.fixture
    def caching_queues_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.queues(mock_original)

    async def test_queues_list_calls_original_with_auth(
        self,
        caching_queues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_queues_protocol.queues_list(
            per_page=50, page=2, auth=yandex_auth
        )

        mock_original.queues_list.assert_called_once_with(
            per_page=50, page=2, auth=yandex_auth
        )
        assert result == mock_original.queues_list.return_value

    async def test_queues_list_calls_original_without_auth(
        self, caching_queues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_queues_protocol.queues_list(per_page=100, page=1)

        mock_original.queues_list.assert_called_once_with(
            per_page=100, page=1, auth=None
        )
        assert result == mock_original.queues_list.return_value

    async def test_queues_get_local_fields_calls_original(
        self,
        caching_queues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_queues_protocol.queues_get_local_fields(
            "TEST", auth=yandex_auth
        )

        mock_original.queues_get_local_fields.assert_called_once_with(
            "TEST", auth=yandex_auth
        )
        assert result == mock_original.queues_get_local_fields.return_value

    async def test_queues_get_tags_calls_original(
        self, caching_queues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_queues_protocol.queues_get_tags("TEST")

        mock_original.queues_get_tags.assert_called_once_with("TEST", auth=None)
        assert result == mock_original.queues_get_tags.return_value

    async def test_queues_get_versions_calls_original(
        self, caching_queues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_queues_protocol.queues_get_versions("TEST")

        mock_original.queues_get_versions.assert_called_once_with("TEST", auth=None)
        assert result == mock_original.queues_get_versions.return_value

    async def test_queues_get_fields_calls_original(
        self,
        caching_queues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_queues_protocol.queues_get_fields(
            "TEST", auth=yandex_auth
        )

        mock_original.queues_get_fields.assert_called_once_with(
            "TEST", auth=yandex_auth
        )
        assert result == mock_original.queues_get_fields.return_value

    async def test_queues_get_fields_calls_original_without_auth(
        self, caching_queues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_queues_protocol.queues_get_fields("TEST")

        mock_original.queues_get_fields.assert_called_once_with("TEST", auth=None)
        assert result == mock_original.queues_get_fields.return_value

    async def test_queue_get_calls_original(
        self,
        caching_queues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_queues_protocol.queue_get("TEST", auth=yandex_auth)

        mock_original.queue_get.assert_called_once_with(
            "TEST", expand=None, auth=yandex_auth
        )
        assert result == mock_original.queue_get.return_value

    async def test_queue_get_calls_original_with_expand(
        self, caching_queues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_queues_protocol.queue_get(
            "TEST", expand=["all", "projects"]
        )

        mock_original.queue_get.assert_called_once_with(
            "TEST", expand=["all", "projects"], auth=None
        )
        assert result == mock_original.queue_get.return_value
