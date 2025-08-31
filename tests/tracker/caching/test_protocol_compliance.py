import inspect
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol


class TestCachingProtocolCompliance:
    """Test that cached protocol implementations properly implement protocol interfaces."""

    @pytest.fixture
    def cache_config(self):
        """Cache configuration for testing."""
        return {"ttl": 300}

    @pytest.fixture
    def cached_protocols(self, cache_config):
        """Create cached protocol classes."""
        return make_cached_protocols(cache_config)

    @pytest.fixture
    def mock_original(self):
        """Create a mock original implementation."""
        return AsyncMock()

    def test_caching_queues_protocol_implements_interface(
        self, cached_protocols, mock_original
    ):
        """Test that CachingQueuesProtocol implements QueuesProtocol."""
        queues_class, _, _, _ = cached_protocols
        caching_queues = queues_class(mock_original)

        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(QueuesProtocol)
        for method_name in protocol_methods:
            assert hasattr(caching_queues, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(caching_queues, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    def test_caching_issues_protocol_implements_interface(
        self, cached_protocols, mock_original
    ):
        """Test that CachingIssuesProtocol implements IssueProtocol."""
        _, issues_class, _, _ = cached_protocols
        caching_issues = issues_class(mock_original)

        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(IssueProtocol)
        for method_name in protocol_methods:
            assert hasattr(caching_issues, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(caching_issues, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    def test_caching_global_data_protocol_implements_interface(
        self, cached_protocols, mock_original
    ):
        """Test that CachingGlobalDataProtocol implements GlobalDataProtocol."""
        _, _, global_data_class, _ = cached_protocols
        caching_global_data = global_data_class(mock_original)

        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(GlobalDataProtocol)
        for method_name in protocol_methods:
            assert hasattr(caching_global_data, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(caching_global_data, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    def test_caching_users_protocol_implements_interface(
        self, cached_protocols, mock_original
    ):
        """Test that CachingUsersProtocol implements UsersProtocol."""
        _, _, _, users_class = cached_protocols
        caching_users = users_class(mock_original)

        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(UsersProtocol)
        for method_name in protocol_methods:
            assert hasattr(caching_users, method_name), f"Missing method: {method_name}"
            # Verify method is callable
            method = getattr(caching_users, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    def test_caching_queues_method_signatures(self, cached_protocols, mock_original):
        """Test that CachingQueuesProtocol method signatures match protocol."""
        queues_class, _, _, _ = cached_protocols
        caching_queues = queues_class(mock_original)
        self._verify_method_signatures(caching_queues, QueuesProtocol)

    def test_caching_issues_method_signatures(self, cached_protocols, mock_original):
        """Test that CachingIssuesProtocol method signatures match protocol."""
        _, issues_class, _, _ = cached_protocols
        caching_issues = issues_class(mock_original)
        self._verify_method_signatures(caching_issues, IssueProtocol)

    def test_caching_global_data_method_signatures(
        self, cached_protocols, mock_original
    ):
        """Test that CachingGlobalDataProtocol method signatures match protocol."""
        _, _, global_data_class, _ = cached_protocols
        caching_global_data = global_data_class(mock_original)
        self._verify_method_signatures(caching_global_data, GlobalDataProtocol)

    def test_caching_users_method_signatures(self, cached_protocols, mock_original):
        """Test that CachingUsersProtocol method signatures match protocol."""
        _, _, _, users_class = cached_protocols
        caching_users = users_class(mock_original)
        self._verify_method_signatures(caching_users, UsersProtocol)

    def _get_protocol_methods(self, protocol_class) -> list[str]:
        """Get all method names defined in a protocol."""
        methods = []
        for name, value in inspect.getmembers(protocol_class):
            if (
                inspect.isfunction(value)
                or inspect.ismethod(value)
                or (hasattr(value, "__annotations__") and callable(value))
            ):
                if not name.startswith("_"):  # Skip private methods
                    methods.append(name)
        return methods

    def _verify_method_signatures(self, implementation, protocol_class):
        """Verify that implementation method signatures match protocol."""
        protocol_methods = self._get_protocol_methods(protocol_class)

        for method_name in protocol_methods:
            if not hasattr(implementation, method_name):
                continue  # Skip if method doesn't exist (will be caught by other tests)

            impl_method = getattr(implementation, method_name)
            protocol_method = getattr(protocol_class, method_name)

            # Get signatures
            impl_sig = inspect.signature(impl_method)
            protocol_sig = inspect.signature(protocol_method)

            # Compare parameter names and types
            impl_params = list(impl_sig.parameters.keys())
            protocol_params = list(protocol_sig.parameters.keys())

            # Skip 'self' parameter for comparison
            if "self" in impl_params:
                impl_params.remove("self")
            if "self" in protocol_params:
                protocol_params.remove("self")

            assert impl_params == protocol_params, (
                f"Method {method_name}: parameter mismatch. "
                f"Implementation: {impl_params}, Protocol: {protocol_params}"
            )


class TestCachingProtocolAuthParameterDelegation:
    """Test that cached protocols properly delegate auth parameters to original implementations."""

    @pytest.fixture
    def cache_config(self):
        return {"ttl": 300}

    @pytest.fixture
    def cached_protocols(self, cache_config):
        return make_cached_protocols(cache_config)

    @pytest.fixture
    def mock_original(self):
        return AsyncMock()

    async def test_queues_methods_delegate_auth_parameter(
        self, cached_protocols, mock_original
    ):
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
        self, cached_protocols, mock_original
    ):
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
        self, cached_protocols, mock_original
    ):
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
        self, cached_protocols, mock_original
    ):
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
        self, cached_protocols, mock_original
    ):
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
    def cache_config(self):
        return {"ttl": 300}

    @pytest.fixture
    def cached_protocols(self, cache_config):
        return make_cached_protocols(cache_config)

    @pytest.fixture
    def mock_original(self):
        return AsyncMock()

    def test_all_queues_methods_are_cached(self, cached_protocols, mock_original):
        """Test that all QueuesProtocol methods are decorated with caching."""
        queues_class, _, _, _ = cached_protocols
        caching_queues = queues_class(mock_original)

        protocol_methods = self._get_protocol_methods(QueuesProtocol)
        for method_name in protocol_methods:
            method = getattr(caching_queues, method_name)
            # Check if method has caching attributes (this is a basic check)
            assert hasattr(method, "__wrapped__") or hasattr(method, "_cache"), (
                f"Method {method_name} should be cached"
            )

    def test_all_issues_methods_are_cached(self, cached_protocols, mock_original):
        """Test that all IssueProtocol methods are decorated with caching."""
        _, issues_class, _, _ = cached_protocols
        caching_issues = issues_class(mock_original)

        protocol_methods = self._get_protocol_methods(IssueProtocol)
        for method_name in protocol_methods:
            method = getattr(caching_issues, method_name)
            # Check if method has caching attributes (this is a basic check)
            assert hasattr(method, "__wrapped__") or hasattr(method, "_cache"), (
                f"Method {method_name} should be cached"
            )

    def test_all_global_data_methods_are_cached(self, cached_protocols, mock_original):
        """Test that all GlobalDataProtocol methods are decorated with caching."""
        _, _, global_data_class, _ = cached_protocols
        caching_global_data = global_data_class(mock_original)

        protocol_methods = self._get_protocol_methods(GlobalDataProtocol)
        for method_name in protocol_methods:
            method = getattr(caching_global_data, method_name)
            # Check if method has caching attributes (this is a basic check)
            assert hasattr(method, "__wrapped__") or hasattr(method, "_cache"), (
                f"Method {method_name} should be cached"
            )

    def test_all_users_methods_are_cached(self, cached_protocols, mock_original):
        """Test that all UsersProtocol methods are decorated with caching."""
        _, _, _, users_class = cached_protocols
        caching_users = users_class(mock_original)

        protocol_methods = self._get_protocol_methods(UsersProtocol)
        for method_name in protocol_methods:
            method = getattr(caching_users, method_name)
            # Check if method has caching attributes (this is a basic check)
            assert hasattr(method, "__wrapped__") or hasattr(method, "_cache"), (
                f"Method {method_name} should be cached"
            )

    def _get_protocol_methods(self, protocol_class) -> list[str]:
        """Get all method names defined in a protocol."""
        methods = []
        for name, value in inspect.getmembers(protocol_class):
            if (
                inspect.isfunction(value)
                or inspect.ismethod(value)
                or (hasattr(value, "__annotations__") and callable(value))
            ):
                if not name.startswith("_"):  # Skip private methods
                    methods.append(name)
        return methods
