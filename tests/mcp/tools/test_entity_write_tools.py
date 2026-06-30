from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.entities import Entity
from tests.mcp.conftest import get_tool_result_content


class TestEntityCreate:
    async def test_creates_entity(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        created = Entity.model_construct(
            id="6a43e17349b4e74442327d7f",
            version=1,
            shortId=22,
            entityType="project",
        )
        mock_entities_protocol.entity_create.return_value = created

        result = await client_session.call_tool(
            "entity_create",
            {
                "entity_type": "project",
                "summary": "New Project",
            },
        )

        assert not result.isError
        mock_entities_protocol.entity_create.assert_called_once()
        call_args = mock_entities_protocol.entity_create.call_args
        assert call_args.args[0] == "project"
        assert call_args.kwargs["summary"] == "New Project"

        content = get_tool_result_content(result)
        assert content["id"] == created.id
        assert content["shortId"] == created.shortId

    async def test_create_with_extra_fields(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        created = Entity.model_construct(id="g-1", entityType="goal")
        mock_entities_protocol.entity_create.return_value = created

        result = await client_session.call_tool(
            "entity_create",
            {
                "entity_type": "goal",
                "summary": "Goal",
                "fields": {"lead": "j.doe"},
            },
        )

        assert not result.isError
        call_args = mock_entities_protocol.entity_create.call_args
        assert call_args.kwargs["fields"] == {"lead": "j.doe"}


class TestEntityDelete:
    async def test_deletes_entity(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        mock_entities_protocol.entity_delete.return_value = None

        result = await client_session.call_tool(
            "entity_delete",
            {
                "entity_type": "project",
                "entity_id": "ent-123",
            },
        )

        assert not result.isError
        mock_entities_protocol.entity_delete.assert_called_once()
        call_args = mock_entities_protocol.entity_delete.call_args
        assert call_args.args[0] == "project"
        assert call_args.args[1] == "ent-123"

    async def test_not_registered_in_read_only(
        self,
        client_session_read_only: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "entity_delete",
            {"entity_type": "project", "entity_id": "ent-123"},
        )

        assert result.isError
        mock_entities_protocol.entity_delete.assert_not_called()
