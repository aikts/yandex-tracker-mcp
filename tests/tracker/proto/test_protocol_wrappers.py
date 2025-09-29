import inspect

import pytest

from mcp_tracker.tracker.proto.fields import GlobalDataProtocol, GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocol, IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocol, QueuesProtocolWrap
from mcp_tracker.tracker.proto.users import UsersProtocol, UsersProtocolWrap


class TestProtocolWrapperBase:
    """Test the base functionality of protocol wrapper classes."""

    @pytest.mark.parametrize(
        "wrapper_class",
        [
            QueuesProtocolWrap,
            IssueProtocolWrap,
            GlobalDataProtocolWrap,
            UsersProtocolWrap,
        ],
    )
    def test_protocol_wrap_has_init_method(self, wrapper_class: type) -> None:
        """Test that protocol wrapper classes have proper __init__ method signature."""
        init_method = wrapper_class.__init__  # type: ignore[misc]
        sig = inspect.signature(init_method)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "original" in params


class TestProtocolWrapperInheritance:
    """Test that protocol wrapper classes properly inherit from their respective protocols."""

    @pytest.mark.parametrize(
        "protocol_class,wrapper_class",
        [
            (QueuesProtocol, QueuesProtocolWrap),
            (IssueProtocol, IssueProtocolWrap),
            (GlobalDataProtocol, GlobalDataProtocolWrap),
            (UsersProtocol, UsersProtocolWrap),
        ],
    )
    def test_protocol_wrap_has_protocol_methods(
        self,
        protocol_class: type,
        wrapper_class: type,
    ) -> None:
        """Test that protocol wrapper classes have all protocol methods."""
        protocol_methods = self._get_protocol_methods(protocol_class)
        for method_name in protocol_methods:
            assert hasattr(wrapper_class, method_name), (
                f"{wrapper_class.__name__} missing method: {method_name}"
            )

    def _get_protocol_methods(self, protocol_class: type) -> list[str]:
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
