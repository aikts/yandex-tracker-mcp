from unittest.mock import AsyncMock

from mcp import Client
from mcp.types import TextContent

from mcp_tracker.tracker.proto.types.components import Component
from tests.mcp.conftest import get_tool_result_content
from tests.mcp.tools.conftest import component_in


class TestComponentGet:
    async def test_returns_component(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_component

        result = await client_session.call_tool("component_get", {"component_id": 856})

        assert not result.is_error
        mock_components_protocol.component_get.assert_called_once()
        call_args = mock_components_protocol.component_get.call_args
        assert call_args.args[0] == 856
        assert "auth" in call_args.kwargs

        content = get_tool_result_content(result)
        assert content["id"] == 856
        assert content["version"] == 1
        assert content["name"] == "Design"
        assert content["queue"]["key"] == "TEST"
        assert content["lead"]["id"] == "i.ivanov"
        assert content["assignAuto"] is False

    async def test_restricted_queue_is_rejected_after_the_read(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        """The id names no queue, so the check can only run on what came back."""
        mock_components_protocol.component_get.return_value = component_in("RESTRICTED")

        result = await client_session_with_limits.call_tool(
            "component_get", {"component_id": 856}
        )

        assert result.is_error
        mock_components_protocol.component_get.assert_called_once()
        # Reported as not found, without naming the queue the allow-list hides.
        error = result.content[0]
        assert isinstance(error, TextContent)
        assert "not found" in error.text
        assert "RESTRICTED" not in error.text

    async def test_allowed_queue_passes(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("ALLOWED")

        result = await client_session_with_limits.call_tool(
            "component_get", {"component_id": 856}
        )

        assert not result.is_error
        content = get_tool_result_content(result)
        assert content["queue"]["key"] == "ALLOWED"
