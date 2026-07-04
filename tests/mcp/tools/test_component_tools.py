from typing import Any
from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.components import Component
from mcp_tracker.tracker.proto.types.refs import QueueReference
from tests.mcp.conftest import get_tool_result_content


class TestComponentsGetAll:
    async def test_gets_all_components(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        other_component = Component.model_construct(
            id=111176,
            name="Other Component",
            description="Another component",
            queue=QueueReference(id="67890", key="OTHER", display="Other Queue"),
        )
        mock_components_protocol.components_list.side_effect = [
            [sample_queue_component, other_component],
            [],
        ]

        result = await client_session.call_tool(
            "components_get_all",
            {},
        )

        assert not result.isError
        assert mock_components_protocol.components_list.call_count == 2
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["name"] == sample_queue_component.name
        assert content[1]["name"] == other_component.name

    async def test_filters_by_queue_id(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
        sample_queue_component: Component,
    ) -> None:
        other_component = Component.model_construct(
            id=111176,
            name="Other Component",
            queue=QueueReference(id="67890", key="OTHER", display="Other Queue"),
        )
        mock_components_protocol.components_list.side_effect = [
            [sample_queue_component, other_component],
            [],
        ]

        result = await client_session.call_tool(
            "components_get_all",
            {"queue_id": "TEST"},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["name"] == sample_queue_component.name

    async def test_restricted_queue_filter_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "components_get_all",
            {"queue_id": "RESTRICTED"},
        )

        assert result.isError
        mock_components_protocol.components_list.assert_not_called()

    async def test_applies_queue_limits(
        self,
        client_session_with_limits: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        allowed_component = Component.model_construct(
            id=111175,
            name="Allowed",
            queue=QueueReference(id="1", key="ALLOWED", display="Allowed Queue"),
        )
        restricted_component = Component.model_construct(
            id=111176,
            name="Restricted",
            queue=QueueReference(id="2", key="RESTRICTED", display="Restricted Queue"),
        )
        mock_components_protocol.components_list.side_effect = [
            [allowed_component, restricted_component],
            [],
        ]

        result = await client_session_with_limits.call_tool(
            "components_get_all",
            {},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["name"] == "Allowed"

    async def test_fetches_multiple_pages(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        page1_component = Component.model_construct(
            id=111175,
            name="Page 1",
            queue=QueueReference(id="1", key="TEST", display="Test Queue"),
        )
        page2_component = Component.model_construct(
            id=111176,
            name="Page 2",
            queue=QueueReference(id="1", key="TEST", display="Test Queue"),
        )
        call_count = 0

        async def side_effect(*args: Any, **kwargs: Any) -> list[Component]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [page1_component]
            if call_count == 2:
                return [page2_component]
            return []

        mock_components_protocol.components_list.side_effect = side_effect

        result = await client_session.call_tool(
            "components_get_all",
            {},
        )

        assert not result.isError
        assert call_count == 3
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["name"] == "Page 1"
        assert content[1]["name"] == "Page 2"

    async def test_fetches_specific_page(
        self,
        client_session: ClientSession,
        mock_components_protocol: AsyncMock,
    ) -> None:
        page2_component = Component.model_construct(
            id=111176,
            name="Page 2",
            queue=QueueReference(id="1", key="TEST", display="Test Queue"),
        )
        mock_components_protocol.components_list.return_value = [page2_component]

        result = await client_session.call_tool(
            "components_get_all",
            {"page": 2, "per_page": 10},
        )

        assert not result.isError
        mock_components_protocol.components_list.assert_called_once()
        call_kwargs = mock_components_protocol.components_list.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["per_page"] == 10
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["name"] == "Page 2"


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
