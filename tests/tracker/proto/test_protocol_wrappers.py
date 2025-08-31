import inspect

from mcp_tracker.tracker.proto.fields import GlobalDataProtocol, GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocol, IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocol, QueuesProtocolWrap
from mcp_tracker.tracker.proto.users import UsersProtocol, UsersProtocolWrap


class TestProtocolWrapperBase:
    """Test the base functionality of protocol wrapper classes."""

    def test_queues_protocol_wrap_has_init_method(self):
        """Test that QueuesProtocolWrap has proper __init__ method signature."""
        init_method = QueuesProtocolWrap.__init__
        sig = inspect.signature(init_method)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "original" in params

    def test_issues_protocol_wrap_has_init_method(self):
        """Test that IssueProtocolWrap has proper __init__ method signature."""
        init_method = IssueProtocolWrap.__init__
        sig = inspect.signature(init_method)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "original" in params

    def test_global_data_protocol_wrap_has_init_method(self):
        """Test that GlobalDataProtocolWrap has proper __init__ method signature."""
        init_method = GlobalDataProtocolWrap.__init__
        sig = inspect.signature(init_method)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "original" in params

    def test_users_protocol_wrap_has_init_method(self):
        """Test that UsersProtocolWrap has proper __init__ method signature."""
        init_method = UsersProtocolWrap.__init__
        sig = inspect.signature(init_method)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "original" in params


class TestProtocolWrapperInheritance:
    """Test that protocol wrapper classes properly inherit from their respective protocols."""

    def test_queues_protocol_wrap_has_protocol_methods(self):
        """Test that QueuesProtocolWrap has all QueuesProtocol methods."""
        # Test that all protocol methods are available on the wrapper class
        protocol_methods = self._get_protocol_methods(QueuesProtocol)
        for method_name in protocol_methods:
            assert hasattr(QueuesProtocolWrap, method_name), (
                f"QueuesProtocolWrap missing method: {method_name}"
            )

    def test_issues_protocol_wrap_has_protocol_methods(self):
        """Test that IssueProtocolWrap has all IssueProtocol methods."""
        # Test that all protocol methods are available on the wrapper class
        protocol_methods = self._get_protocol_methods(IssueProtocol)
        for method_name in protocol_methods:
            assert hasattr(IssueProtocolWrap, method_name), (
                f"IssueProtocolWrap missing method: {method_name}"
            )

    def test_global_data_protocol_wrap_has_protocol_methods(self):
        """Test that GlobalDataProtocolWrap has all GlobalDataProtocol methods."""
        # Test that all protocol methods are available on the wrapper class
        protocol_methods = self._get_protocol_methods(GlobalDataProtocol)
        for method_name in protocol_methods:
            assert hasattr(GlobalDataProtocolWrap, method_name), (
                f"GlobalDataProtocolWrap missing method: {method_name}"
            )

    def test_users_protocol_wrap_has_protocol_methods(self):
        """Test that UsersProtocolWrap has all UsersProtocol methods."""
        # Test that all protocol methods are available on the wrapper class
        protocol_methods = self._get_protocol_methods(UsersProtocol)
        for method_name in protocol_methods:
            assert hasattr(UsersProtocolWrap, method_name), (
                f"UsersProtocolWrap missing method: {method_name}"
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
