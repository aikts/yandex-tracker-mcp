from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.components import Component
from mcp_tracker.tracker.proto.types.refs import QueueReference
from tests.mcp.conftest import get_tool_result_content


class TestComponentGet:
    async def test_gets_component(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_get",
            {"component_id": 111175},
        )

        assert not result.isError
        mock_components_protocol.component_get.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["name"] == sample_queue_component.name

    async def test_gets_component_in_read_only_mode(
        self,
        client_session_read_only: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_queue_component

        result = await client_session_read_only.call_tool(
            "component_get",
            {"component_id": 111175},
        )

        assert not result.isError
        mock_components_protocol.component_get.assert_called_once()

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        sample_queue_component.queue = QueueReference(
            id="999", key="RESTRICTED", display="Restricted Queue"
        )
        mock_components_protocol.component_get.return_value = sample_queue_component

        result = await client_session_with_limits.call_tool(
            "component_get",
            {"component_id": 111175},
        )

        assert result.isError


class TestComponentCreate:
    async def test_creates_component(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_create",
            {"queue_id": "TEST", "name": "Test Component"},
        )

        assert not result.isError
        mock_components_protocol.component_create.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["name"] == sample_queue_component.name

    async def test_with_description(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_create",
            {
                "queue_id": "TEST",
                "name": "Test Component",
                "description": "A test component",
            },
        )

        assert not result.isError
        call_kwargs = mock_components_protocol.component_create.call_args.kwargs
        assert call_kwargs["description"] == "A test component"
        content = get_tool_result_content(result)
        assert content["name"] == sample_queue_component.name

    async def test_with_lead_and_assign_auto(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_create",
            {
                "queue_id": "TEST",
                "name": "Test Component",
                "lead": "testuser",
                "assign_auto": True,
            },
        )

        assert not result.isError
        call_kwargs = mock_components_protocol.component_create.call_args.kwargs
        assert call_kwargs["lead"] == "testuser"
        assert call_kwargs["assign_auto"] is True
        content = get_tool_result_content(result)
        assert content["name"] == sample_queue_component.name

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "component_create",
            {"queue_id": "RESTRICTED", "name": "Test"},
        )

        assert result.isError
        mock_components_protocol.component_create.assert_not_called()


class TestComponentUpdate:
    async def test_updates_component(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_queue_component
        mock_components_protocol.component_update.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_update",
            {"component_id": 111175, "name": "Updated Component"},
        )

        assert not result.isError
        mock_components_protocol.component_get.assert_called_once()
        mock_components_protocol.component_update.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["name"] == sample_queue_component.name

    async def test_with_description(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_queue_component
        mock_components_protocol.component_update.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_update",
            {
                "component_id": 111175,
                "name": "Updated",
                "description": "Updated description",
            },
        )

        assert not result.isError
        call_kwargs = mock_components_protocol.component_update.call_args.kwargs
        assert call_kwargs["description"] == "Updated description"
        content = get_tool_result_content(result)
        assert content["name"] == sample_queue_component.name

    async def test_with_lead(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_queue_component
        mock_components_protocol.component_update.return_value = sample_queue_component

        result = await client_session.call_tool(
            "component_update",
            {
                "component_id": 111175,
                "name": "Updated",
                "lead": "newlead",
            },
        )

        assert not result.isError
        call_kwargs = mock_components_protocol.component_update.call_args.kwargs
        assert call_kwargs["lead"] == "newlead"
        content = get_tool_result_content(result)
        assert content["name"] == sample_queue_component.name

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        sample_queue_component.queue = QueueReference(
            id="999", key="RESTRICTED", display="Restricted Queue"
        )
        mock_components_protocol.component_get.return_value = sample_queue_component

        result = await client_session_with_limits.call_tool(
            "component_update",
            {"component_id": 111175, "name": "Updated"},
        )

        assert result.isError
        mock_components_protocol.component_update.assert_not_called()


class TestComponentDelete:
    async def test_deletes_component(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = sample_queue_component
        mock_components_protocol.component_delete.return_value = None

        result = await client_session.call_tool(
            "component_delete",
            {"component_id": 111175},
        )

        assert not result.isError
        mock_components_protocol.component_get.assert_called_once()
        mock_components_protocol.component_delete.assert_called_once()
        call_args = mock_components_protocol.component_delete.call_args
        assert call_args.args[0] == 111175

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        sample_queue_component.queue = QueueReference(
            id="999", key="RESTRICTED", display="Restricted Queue"
        )
        mock_components_protocol.component_get.return_value = sample_queue_component

        result = await client_session_with_limits.call_tool(
            "component_delete",
            {"component_id": 111175},
        )

        assert result.isError
        mock_components_protocol.component_delete.assert_not_called()
