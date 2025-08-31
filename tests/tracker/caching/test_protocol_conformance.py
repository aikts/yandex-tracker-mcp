"""Simple protocol conformance tests for caching classes."""

from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol


class TestCachingProtocolConformance:
    @pytest.fixture
    def cache_config(self) -> dict[str, int]:
        return {"ttl": 300}

    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        return AsyncMock()

    def test_caching_queues_implements_protocol(
        self, cache_config: dict[str, int], mock_original: QueuesProtocol
    ) -> None:
        cache_collection = make_cached_protocols(cache_config)
        instance = cache_collection.queues(mock_original)

        assert isinstance(instance, QueuesProtocol)

    def test_caching_issues_implements_protocol(
        self, cache_config: dict[str, int], mock_original: IssueProtocol
    ) -> None:
        cache_collection = make_cached_protocols(cache_config)
        instance = cache_collection.issues(mock_original)

        assert isinstance(instance, IssueProtocol)

    def test_caching_global_data_implements_protocol(
        self, cache_config: dict[str, int], mock_original: GlobalDataProtocol
    ) -> None:
        cache_collection = make_cached_protocols(cache_config)
        instance = cache_collection.global_data(mock_original)

        assert isinstance(instance, GlobalDataProtocol)

    def test_caching_users_implements_protocol(
        self, cache_config: dict[str, int], mock_original: UsersProtocol
    ) -> None:
        cache_collection = make_cached_protocols(cache_config)
        instance = cache_collection.users(mock_original)

        assert isinstance(instance, UsersProtocol)
