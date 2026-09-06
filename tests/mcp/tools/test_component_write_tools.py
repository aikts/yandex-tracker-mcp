from unittest.mock import AsyncMock

import pytest
from mcp import Client

from mcp_tracker.tracker.proto.types.components import Component
from tests.mcp.conftest import get_tool_result_content
from tests.mcp.tools.conftest import component_in


class TestComponentCreate:
    async def test_creates_component(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_component

        result = await client_session.call_tool(
            "component_create",
            {
                "queue_id": "TEST",
                "name": "Design",
                "description": "Design work",
                "lead": "i.ivanov",
                "assign_auto": True,
            },
        )

        assert not result.is_error
        mock_components_protocol.component_create.assert_called_once()
        call_args = mock_components_protocol.component_create.call_args
        assert call_args.args[0] == "TEST"
        assert call_args.kwargs["name"] == "Design"
        assert call_args.kwargs["description"] == "Design work"
        assert call_args.kwargs["lead"] == "i.ivanov"
        assert call_args.kwargs["assign_auto"] is True
        assert "auth" in call_args.kwargs

        content = get_tool_result_content(result)
        assert content["id"] == sample_component.id
        assert content["name"] == sample_component.name

    async def test_optional_parameters_omitted(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_component

        result = await client_session.call_tool(
            "component_create", {"queue_id": "TEST", "name": "Design"}
        )

        assert not result.is_error
        call_args = mock_components_protocol.component_create.call_args
        assert call_args.kwargs["description"] is None
        assert call_args.kwargs["lead"] is None
        assert call_args.kwargs["assign_auto"] is None

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "component_create", {"queue_id": "TEST", "name": "Design"}
        )

        assert result.is_error
        mock_components_protocol.component_create.assert_not_called()

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "component_create", {"queue_id": "RESTRICTED", "name": "Design"}
        )

        assert result.is_error
        mock_components_protocol.component_create.assert_not_called()

    async def test_read_only_queue_rejected(
        self,
        client_session_with_read_only_queues: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_read_only_queues.call_tool(
            "component_create", {"queue_id": "READONLY", "name": "Design"}
        )

        assert result.is_error
        mock_components_protocol.component_create.assert_not_called()

    async def test_writable_queue_allowed(
        self,
        client_session_with_read_only_queues: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_create.return_value = sample_component

        result = await client_session_with_read_only_queues.call_tool(
            "component_create", {"queue_id": "TEST", "name": "Design"}
        )

        assert not result.is_error
        mock_components_protocol.component_create.assert_called_once()


class TestComponentUpdate:
    async def test_updates_component(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session.call_tool(
            "component_update",
            {
                "component_id": 856,
                "name": "Design",
                "description": "Design work",
                "lead": "i.ivanov",
                "assign_auto": True,
                "version": 1,
            },
        )

        assert not result.is_error
        mock_components_protocol.component_update.assert_called_once()
        call_args = mock_components_protocol.component_update.call_args
        assert call_args.args[0] == 856
        assert call_args.kwargs["version"] == 1
        assert call_args.kwargs["name"] == "Design"
        assert call_args.kwargs["description"] == "Design work"
        assert call_args.kwargs["lead"] == "i.ivanov"
        assert call_args.kwargs["assign_auto"] is True
        assert "auth" in call_args.kwargs

        content = get_tool_result_content(result)
        assert content["id"] == sample_component.id

    async def test_optional_parameters_omitted(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        """The client, not the tool, refuses an empty update - so the tool
        passes the arguments on exactly as given."""
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session.call_tool(
            "component_update", {"component_id": 856, "version": 1, "name": "Design"}
        )

        assert not result.is_error
        call_args = mock_components_protocol.component_update.call_args
        assert call_args.kwargs["name"] == "Design"
        assert call_args.kwargs["description"] is None
        assert call_args.kwargs["lead"] is None
        assert call_args.kwargs["assign_auto"] is None
        assert call_args.kwargs["clear_lead"] is False

    async def test_clear_lead_is_passed_through(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session.call_tool(
            "component_update", {"component_id": 856, "version": 1, "clear_lead": True}
        )

        assert not result.is_error
        call_args = mock_components_protocol.component_update.call_args
        assert call_args.kwargs["clear_lead"] is True
        assert call_args.kwargs["lead"] is None

    async def test_a_given_version_skips_the_read_on_an_unrestricted_server(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session.call_tool(
            "component_update", {"component_id": 856, "name": "Design", "version": 7}
        )

        assert not result.is_error
        mock_components_protocol.component_get.assert_not_called()
        assert (
            mock_components_protocol.component_update.call_args.kwargs["version"] == 7
        )

    async def test_without_a_version_the_component_is_read_once(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in(
            "TEST", version=4
        )
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session.call_tool(
            "component_update", {"component_id": 856, "name": "Design"}
        )

        assert not result.is_error
        mock_components_protocol.component_get.assert_called_once()
        assert mock_components_protocol.component_get.call_args.args[0] == 856
        # The version the read returned is what the update sends.
        assert (
            mock_components_protocol.component_update.call_args.kwargs["version"] == 4
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "component_update", {"component_id": 856, "name": "Design"}
        )

        assert result.is_error
        mock_components_protocol.component_update.assert_not_called()

    @pytest.mark.parametrize("arguments", [{}, {"version": 7}])
    async def test_restricted_queue_is_rejected_after_one_read(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
        arguments: dict[str, int],
    ) -> None:
        """Under `TRACKER_LIMIT_QUEUES` the read happens even with a version given."""
        mock_components_protocol.component_get.return_value = component_in("RESTRICTED")

        result = await client_session_with_limits.call_tool(
            "component_update", {"component_id": 856, "name": "Design", **arguments}
        )

        assert result.is_error
        mock_components_protocol.component_get.assert_called_once()
        mock_components_protocol.component_update.assert_not_called()

    async def test_allowed_queue_passes_with_the_given_version(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("ALLOWED")
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session_with_limits.call_tool(
            "component_update", {"component_id": 856, "name": "Design", "version": 7}
        )

        assert not result.is_error
        mock_components_protocol.component_get.assert_called_once()
        # A version the caller gave is not replaced by the one read.
        assert (
            mock_components_protocol.component_update.call_args.kwargs["version"] == 7
        )

    async def test_read_only_queue_rejected(
        self,
        client_session_with_read_only_queues: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("READONLY")

        result = await client_session_with_read_only_queues.call_tool(
            "component_update", {"component_id": 856, "name": "Design", "version": 7}
        )

        assert result.is_error
        mock_components_protocol.component_get.assert_called_once()
        mock_components_protocol.component_update.assert_not_called()

    async def test_writable_queue_allowed(
        self,
        client_session_with_read_only_queues: Client,
        mock_components_protocol: AsyncMock,
        sample_component: Component,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("TEST")
        mock_components_protocol.component_update.return_value = sample_component

        result = await client_session_with_read_only_queues.call_tool(
            "component_update", {"component_id": 856, "name": "Design"}
        )

        assert not result.is_error
        mock_components_protocol.component_update.assert_called_once()


class TestComponentDelete:
    async def test_deletes_component(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_delete.return_value = None

        result = await client_session.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert not result.is_error
        mock_components_protocol.component_delete.assert_called_once()
        call_args = mock_components_protocol.component_delete.call_args
        assert call_args.args[0] == 856
        assert "auth" in call_args.kwargs

    async def test_unrestricted_server_does_not_read_the_component(
        self,
        client_session: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_delete.return_value = None

        result = await client_session.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert not result.is_error
        mock_components_protocol.component_get.assert_not_called()

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert result.is_error
        mock_components_protocol.component_delete.assert_not_called()

    async def test_restricted_queue_is_rejected_after_one_read(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("RESTRICTED")

        result = await client_session_with_limits.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert result.is_error
        mock_components_protocol.component_get.assert_called_once()
        mock_components_protocol.component_delete.assert_not_called()

    async def test_allowed_queue_is_deleted_after_one_read(
        self,
        client_session_with_limits: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("ALLOWED")
        mock_components_protocol.component_delete.return_value = None

        result = await client_session_with_limits.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert not result.is_error
        mock_components_protocol.component_get.assert_called_once()
        mock_components_protocol.component_delete.assert_called_once()

    async def test_read_only_queue_rejected(
        self,
        client_session_with_read_only_queues: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("READONLY")

        result = await client_session_with_read_only_queues.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert result.is_error
        mock_components_protocol.component_delete.assert_not_called()

    async def test_writable_queue_allowed(
        self,
        client_session_with_read_only_queues: Client,
        mock_components_protocol: AsyncMock,
    ) -> None:
        mock_components_protocol.component_get.return_value = component_in("TEST")
        mock_components_protocol.component_delete.return_value = None

        result = await client_session_with_read_only_queues.call_tool(
            "component_delete", {"component_id": 856}
        )

        assert not result.is_error
        mock_components_protocol.component_delete.assert_called_once()
