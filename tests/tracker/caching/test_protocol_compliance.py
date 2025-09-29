from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol
from tests.protocol_utils import get_protocol_methods, verify_method_signatures


class TestCachingProtocolCompliance:
    """Test that cached protocol implementations properly implement protocol interfaces."""

    @pytest.fixture
    def cache_config(self) -> dict[str, int]:
        """Cache configuration for testing."""
        return {"ttl": 300}

    @pytest.fixture
    def cached_protocols(
        self, cache_config: dict[str, int]
    ) -> tuple[Any, Any, Any, Any]:
        """Create cached protocol classes."""
        return make_cached_protocols(cache_config)

    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        """Create a mock original implementation."""
        return AsyncMock()

    @pytest.mark.parametrize(
        "protocol_class,protocol_index",
        [
            (QueuesProtocol, 0),
            (IssueProtocol, 1),
            (GlobalDataProtocol, 2),
            (UsersProtocol, 3),
        ],
    )
    def test_caching_protocol_implements_interface(
        self,
        cached_protocols: tuple[Any, Any, Any, Any],
        mock_original: AsyncMock,
        protocol_class: type,
        protocol_index: int,
    ) -> None:
        """Test that caching protocol implementations implement protocol interfaces."""
        caching_class = cached_protocols[protocol_index]
        caching_instance = caching_class(mock_original)

        protocol_methods = get_protocol_methods(protocol_class)
        for method_name in protocol_methods:
            assert hasattr(caching_instance, method_name), (
                f"Missing method: {method_name}"
            )
            method = getattr(caching_instance, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    @pytest.mark.parametrize(
        "protocol_class,protocol_index",
        [
            (QueuesProtocol, 0),
            (IssueProtocol, 1),
            (GlobalDataProtocol, 2),
            (UsersProtocol, 3),
        ],
    )
    def test_caching_method_signatures(
        self,
        cached_protocols: tuple[Any, Any, Any, Any],
        mock_original: AsyncMock,
        protocol_class: type,
        protocol_index: int,
    ) -> None:
        """Test that caching protocol method signatures match protocol."""
        caching_class = cached_protocols[protocol_index]
        caching_instance = caching_class(mock_original)
        verify_method_signatures(caching_instance, protocol_class)


class TestCachingProtocolAuthParameterDelegation:
    """Test that cached protocols properly delegate auth parameters to original implementations."""

    @pytest.fixture
    def cache_config(self) -> dict[str, int]:
        return {"ttl": 300}

    @pytest.fixture
    def cached_protocols(
        self, cache_config: dict[str, int]
    ) -> tuple[Any, Any, Any, Any]:
        return make_cached_protocols(cache_config)

    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        return AsyncMock()

    async def test_queues_methods_delegate_auth_parameter(
        self, cached_protocols: tuple[Any, Any, Any, Any], mock_original: AsyncMock
    ) -> None:
        """Test that QueuesProtocol caching methods delegate auth parameter correctly."""
        queues_class, _, _, _ = cached_protocols
        caching_queues = queues_class(mock_original)

        auth = YandexAuth(token="test-token", org_id="test-org")

        # Test queues_list
        await caching_queues.queues_list(per_page=50, page=2, auth=auth)
        mock_original.queues_list.assert_called_with(per_page=50, page=2, auth=auth)

        # Test queues_get_local_fields
        mock_original.reset_mock()
        await caching_queues.queues_get_local_fields("TEST", auth=auth)
        mock_original.queues_get_local_fields.assert_called_with("TEST", auth=auth)

        # Test queues_get_tags
        mock_original.reset_mock()
        await caching_queues.queues_get_tags("TEST", auth=auth)
        mock_original.queues_get_tags.assert_called_with("TEST", auth=auth)

        # Test queues_get_versions
        mock_original.reset_mock()
        await caching_queues.queues_get_versions("TEST", auth=auth)
        mock_original.queues_get_versions.assert_called_with("TEST", auth=auth)

    async def test_issues_methods_delegate_auth_parameter(
        self, cached_protocols: tuple[Any, Any, Any, Any], mock_original: AsyncMock
    ) -> None:
        """Test that IssueProtocol caching methods delegate auth parameter correctly."""
        _, issues_class, _, _ = cached_protocols
        caching_issues = issues_class(mock_original)

        auth = YandexAuth(token="test-token", org_id="test-org")

        # Test issue_get
        await caching_issues.issue_get("TEST-1", auth=auth)
        mock_original.issue_get.assert_called_with("TEST-1", auth=auth)

        # Test issues_get_links
        mock_original.reset_mock()
        await caching_issues.issues_get_links("TEST-1", auth=auth)
        mock_original.issues_get_links.assert_called_with("TEST-1", auth=auth)

        # Test issue_get_comments
        mock_original.reset_mock()
        await caching_issues.issue_get_comments("TEST-1", auth=auth)
        mock_original.issue_get_comments.assert_called_with("TEST-1", auth=auth)

        # Test issues_find
        mock_original.reset_mock()
        await caching_issues.issues_find("query", per_page=20, page=3, auth=auth)
        mock_original.issues_find.assert_called_with(
            query="query", per_page=20, page=3, auth=auth
        )

        # Test issue_get_worklogs
        mock_original.reset_mock()
        await caching_issues.issue_get_worklogs("TEST-1", auth=auth)
        mock_original.issue_get_worklogs.assert_called_with("TEST-1", auth=auth)

        # Test issue_get_attachments
        mock_original.reset_mock()
        await caching_issues.issue_get_attachments("TEST-1", auth=auth)
        mock_original.issue_get_attachments.assert_called_with("TEST-1", auth=auth)

        # Test issues_count
        mock_original.reset_mock()
        await caching_issues.issues_count("test query", auth=auth)
        mock_original.issues_count.assert_called_with("test query", auth=auth)

        # Test issue_get_checklist
        mock_original.reset_mock()
        await caching_issues.issue_get_checklist("TEST-1", auth=auth)
        mock_original.issue_get_checklist.assert_called_with("TEST-1", auth=auth)

    async def test_global_data_methods_delegate_auth_parameter(
        self, cached_protocols: tuple[Any, Any, Any, Any], mock_original: AsyncMock
    ) -> None:
        """Test that GlobalDataProtocol caching methods delegate auth parameter correctly."""
        _, _, global_data_class, _ = cached_protocols
        caching_global_data = global_data_class(mock_original)

        auth = YandexAuth(token="test-token", org_id="test-org")

        # Test get_global_fields
        await caching_global_data.get_global_fields(auth=auth)
        mock_original.get_global_fields.assert_called_with(auth=auth)

        # Test get_statuses
        mock_original.reset_mock()
        await caching_global_data.get_statuses(auth=auth)
        mock_original.get_statuses.assert_called_with(auth=auth)

        # Test get_issue_types
        mock_original.reset_mock()
        await caching_global_data.get_issue_types(auth=auth)
        mock_original.get_issue_types.assert_called_with(auth=auth)

        # Test get_priorities
        mock_original.reset_mock()
        await caching_global_data.get_priorities(auth=auth)
        mock_original.get_priorities.assert_called_with(auth=auth)

    async def test_users_methods_delegate_auth_parameter(
        self, cached_protocols: tuple[Any, Any, Any, Any], mock_original: AsyncMock
    ) -> None:
        """Test that UsersProtocol caching methods delegate auth parameter correctly."""
        _, _, _, users_class = cached_protocols
        caching_users = users_class(mock_original)

        auth = YandexAuth(token="test-token", org_id="test-org")

        # Test users_list
        await caching_users.users_list(per_page=25, page=2, auth=auth)
        mock_original.users_list.assert_called_with(per_page=25, page=2, auth=auth)

        # Test user_get
        mock_original.reset_mock()
        await caching_users.user_get("test_user", auth=auth)
        mock_original.user_get.assert_called_with("test_user", auth=auth)

        # Test user_get_current
        mock_original.reset_mock()
        await caching_users.user_get_current(auth=auth)
        mock_original.user_get_current.assert_called_with(auth=auth)

    async def test_methods_handle_none_auth_parameter(
        self, cached_protocols: tuple[Any, Any, Any, Any], mock_original: AsyncMock
    ) -> None:
        """Test that caching methods properly handle None auth parameter."""
        queues_class, _, _, _ = cached_protocols
        caching_queues = queues_class(mock_original)

        # Test without auth parameter
        await caching_queues.queues_list()
        mock_original.queues_list.assert_called_with(per_page=100, page=1, auth=None)

        # Test with explicit None
        mock_original.reset_mock()
        await caching_queues.queues_list(auth=None)
        mock_original.queues_list.assert_called_with(per_page=100, page=1, auth=None)


class TestCachingProtocolMethodDecoration:
    """Test that all cached protocol methods are properly decorated with caching."""

    @pytest.fixture
    def cache_config(self) -> dict[str, int]:
        return {"ttl": 300}

    @pytest.fixture
    def cached_protocols(
        self, cache_config: dict[str, int]
    ) -> tuple[Any, Any, Any, Any]:
        return make_cached_protocols(cache_config)

    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.parametrize(
        "protocol_class,protocol_index",
        [
            (QueuesProtocol, 0),
            (IssueProtocol, 1),
            (GlobalDataProtocol, 2),
            (UsersProtocol, 3),
        ],
    )
    def test_all_methods_are_cached(
        self,
        cached_protocols: tuple[Any, Any, Any, Any],
        mock_original: AsyncMock,
        protocol_class: type,
        protocol_index: int,
    ) -> None:
        """Test that all protocol methods are decorated with caching."""
        caching_class = cached_protocols[protocol_index]
        caching_instance = caching_class(mock_original)

        protocol_methods = get_protocol_methods(protocol_class)
        for method_name in protocol_methods:
            method = getattr(caching_instance, method_name)
            assert hasattr(method, "__wrapped__") or hasattr(method, "_cache"), (
                f"Method {method_name} should be cached"
            )
