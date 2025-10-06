import pytest

from mcp_tracker.tracker.proto.fields import GlobalDataProtocol, GlobalDataProtocolWrap
from mcp_tracker.tracker.proto.issues import IssueProtocol, IssueProtocolWrap
from mcp_tracker.tracker.proto.queues import QueuesProtocol, QueuesProtocolWrap
from mcp_tracker.tracker.proto.users import UsersProtocol, UsersProtocolWrap
from tests.protocol_utils import get_protocol_methods


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
        protocol_methods = get_protocol_methods(protocol_class)
        for method_name in protocol_methods:
            assert hasattr(wrapper_class, method_name), (
                f"{wrapper_class.__name__} missing method: {method_name}"
            )
