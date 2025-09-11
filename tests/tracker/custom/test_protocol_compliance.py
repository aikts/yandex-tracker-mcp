import inspect
from typing import AsyncGenerator, get_type_hints

import pytest

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol


class TestTrackerClientProtocolCompliance:
    """Test that TrackerClient implements all required protocol interfaces."""

    @pytest.fixture
    async def tracker_client(self) -> AsyncGenerator[TrackerClient, None]:
        """Create a TrackerClient instance for testing."""
        client = TrackerClient(
            token="test-token",
            org_id="test-org",
        )
        yield client
        await client.close()

    async def test_implements_queues_protocol(self, tracker_client):
        """Test that TrackerClient implements QueuesProtocol."""
        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(QueuesProtocol)
        for method_name in protocol_methods:
            assert hasattr(tracker_client, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(tracker_client, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    async def test_implements_issues_protocol(self, tracker_client):
        """Test that TrackerClient implements IssueProtocol."""
        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(IssueProtocol)
        for method_name in protocol_methods:
            assert hasattr(tracker_client, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(tracker_client, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    async def test_implements_global_data_protocol(self, tracker_client):
        """Test that TrackerClient implements GlobalDataProtocol."""
        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(GlobalDataProtocol)
        for method_name in protocol_methods:
            assert hasattr(tracker_client, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(tracker_client, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    async def test_implements_users_protocol(self, tracker_client):
        """Test that TrackerClient implements UsersProtocol."""
        # Check all protocol methods exist
        protocol_methods = self._get_protocol_methods(UsersProtocol)
        for method_name in protocol_methods:
            assert hasattr(tracker_client, method_name), (
                f"Missing method: {method_name}"
            )
            # Verify method is callable
            method = getattr(tracker_client, method_name)
            assert callable(method), f"Method {method_name} is not callable"

    async def test_queues_protocol_method_signatures(self, tracker_client):
        """Test that QueuesProtocol method signatures match implementation."""
        self._verify_method_signatures(tracker_client, QueuesProtocol)

    async def test_issues_protocol_method_signatures(self, tracker_client):
        """Test that IssueProtocol method signatures match implementation."""
        self._verify_method_signatures(tracker_client, IssueProtocol)

    async def test_global_data_protocol_method_signatures(self, tracker_client):
        """Test that GlobalDataProtocol method signatures match implementation."""
        self._verify_method_signatures(tracker_client, GlobalDataProtocol)

    async def test_users_protocol_method_signatures(self, tracker_client):
        """Test that UsersProtocol method signatures match implementation."""
        self._verify_method_signatures(tracker_client, UsersProtocol)

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

            # Verify auth parameter exists and has correct default
            if "auth" in impl_sig.parameters:
                auth_param = impl_sig.parameters["auth"]
                assert auth_param.default is None, (
                    f"Method {method_name}: auth parameter should default to None"
                )


class TestTrackerClientAuthParameterHandling:
    """Test that TrackerClient properly handles auth parameters across all protocol methods."""

    @pytest.fixture
    async def tracker_client(self):
        client = TrackerClient(token="test-token", org_id="test-org")
        yield client
        await client.close()

    @pytest.mark.parametrize(
        "method_name",
        [
            "queues_list",
            "queues_get_local_fields",
            "queues_get_tags",
            "queues_get_versions",
        ],
    )
    async def test_queues_methods_accept_auth_parameter(
        self, tracker_client, method_name
    ):
        """Test that all QueuesProtocol methods accept auth parameter."""
        method = getattr(tracker_client, method_name)
        sig = inspect.signature(method)

        assert "auth" in sig.parameters, f"Method {method_name} missing auth parameter"
        assert sig.parameters["auth"].default is None, (
            f"Method {method_name} auth parameter should default to None"
        )

    @pytest.mark.parametrize(
        "method_name",
        [
            "issue_get",
            "issue_get_comments",
            "issues_get_links",
            "issues_find",
            "issue_get_worklogs",
            "issue_get_attachments",
            "issues_count",
            "issue_get_checklist",
        ],
    )
    async def test_issues_methods_accept_auth_parameter(
        self, tracker_client, method_name
    ):
        """Test that all IssueProtocol methods accept auth parameter."""
        method = getattr(tracker_client, method_name)
        sig = inspect.signature(method)

        assert "auth" in sig.parameters, f"Method {method_name} missing auth parameter"
        assert sig.parameters["auth"].default is None, (
            f"Method {method_name} auth parameter should default to None"
        )

    @pytest.mark.parametrize(
        "method_name",
        ["get_global_fields", "get_statuses", "get_issue_types", "get_priorities"],
    )
    async def test_global_data_methods_accept_auth_parameter(
        self, tracker_client, method_name
    ):
        """Test that all GlobalDataProtocol methods accept auth parameter."""
        method = getattr(tracker_client, method_name)
        sig = inspect.signature(method)

        assert "auth" in sig.parameters, f"Method {method_name} missing auth parameter"
        assert sig.parameters["auth"].default is None, (
            f"Method {method_name} auth parameter should default to None"
        )

    @pytest.mark.parametrize(
        "method_name", ["users_list", "user_get", "user_get_current"]
    )
    async def test_users_methods_accept_auth_parameter(
        self, tracker_client, method_name
    ):
        """Test that all UsersProtocol methods accept auth parameter."""
        method = getattr(tracker_client, method_name)
        sig = inspect.signature(method)

        assert "auth" in sig.parameters, f"Method {method_name} missing auth parameter"
        assert sig.parameters["auth"].default is None, (
            f"Method {method_name} auth parameter should default to None"
        )


class TestTrackerClientReturnTypes:
    """Test that TrackerClient methods return the correct types as defined in protocols."""

    @pytest.fixture
    async def tracker_client(self):
        client = TrackerClient(token="test-token", org_id="test-org")
        yield client
        await client.close()

    async def test_queues_protocol_return_types(self, tracker_client):
        """Test return types for QueuesProtocol methods."""
        # Get type hints from protocol
        protocol_hints = get_type_hints(QueuesProtocol.queues_list)
        impl_hints = get_type_hints(tracker_client.queues_list)

        # Compare return types (this is a basic check - full verification would require runtime testing)
        assert "return" in protocol_hints
        assert "return" in impl_hints

    async def test_method_is_async(self, tracker_client):
        """Test that all protocol methods are properly async."""
        all_protocols = [
            QueuesProtocol,
            IssueProtocol,
            GlobalDataProtocol,
            UsersProtocol,
        ]

        for protocol in all_protocols:
            methods = self._get_protocol_methods(protocol)
            for method_name in methods:
                if hasattr(tracker_client, method_name):
                    method = getattr(tracker_client, method_name)
                    assert inspect.iscoroutinefunction(method), (
                        f"Method {method_name} should be async"
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
