from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status


class TestCachingGlobalDataProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.get_global_fields.return_value = [
            GlobalField(id="status-field", key="status", name="Status")
        ]
        original.get_statuses.return_value = [
            Status(version=1, key="open", name="Open", order=1, type="new")
        ]
        original.get_issue_types.return_value = [
            IssueType(id=1, version=1, key="task", name="Task")
        ]
        original.get_priorities.return_value = [
            Priority(version=1, key="high", name="High", order=1)
        ]
        original.get_resolutions.return_value = [
            Resolution(id=1, key="fixed", name="Fixed")
        ]
        return original

    @pytest.fixture
    def caching_global_data_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.global_data(mock_original)

    async def test_get_global_fields_calls_original(
        self,
        caching_global_data_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_global_data_protocol.get_global_fields(auth=yandex_auth)

        mock_original.get_global_fields.assert_called_once_with(auth=yandex_auth)
        assert result == mock_original.get_global_fields.return_value

    async def test_get_statuses_calls_original(
        self, caching_global_data_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_global_data_protocol.get_statuses()

        mock_original.get_statuses.assert_called_once_with(auth=None)
        assert result == mock_original.get_statuses.return_value

    async def test_get_issue_types_calls_original(
        self, caching_global_data_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_global_data_protocol.get_issue_types()

        mock_original.get_issue_types.assert_called_once_with(auth=None)
        assert result == mock_original.get_issue_types.return_value

    async def test_get_priorities_calls_original(
        self,
        caching_global_data_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_global_data_protocol.get_priorities(auth=yandex_auth)

        mock_original.get_priorities.assert_called_once_with(auth=yandex_auth)
        assert result == mock_original.get_priorities.return_value

    async def test_get_resolutions_calls_original(
        self,
        caching_global_data_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_global_data_protocol.get_resolutions(auth=yandex_auth)

        mock_original.get_resolutions.assert_called_once_with(auth=yandex_auth)
        assert result == mock_original.get_resolutions.return_value

    async def test_get_resolutions_calls_original_without_auth(
        self, caching_global_data_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_global_data_protocol.get_resolutions()

        mock_original.get_resolutions.assert_called_once_with(auth=None)
        assert result == mock_original.get_resolutions.return_value
