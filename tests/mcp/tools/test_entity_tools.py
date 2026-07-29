from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.entities import Entity
from tests.mcp.conftest import get_tool_result_content


class TestEntityGet:
    async def test_gets_entity(
        self, client_session: ClientSession, mock_entities_protocol: AsyncMock
    ) -> None:
        entity = Entity.model_construct(
            id="p-1", shortId=2, entityType="project", fields={"summary": "P"}
        )
        mock_entities_protocol.entity_get.return_value = entity

        result = await client_session.call_tool(
            "entity_get", {"entity_type": "project", "entity_id": "p-1"}
        )

        assert not result.isError
        mock_entities_protocol.entity_get.assert_called_once()
        call_args = mock_entities_protocol.entity_get.call_args
        assert call_args.args[0] == "project"
        assert call_args.args[1] == "p-1"

        content = get_tool_result_content(result)
        assert content["id"] == "p-1"

    async def test_registered_in_read_only(
        self,
        client_session_read_only: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        entity = Entity.model_construct(id="p-1", entityType="project")
        mock_entities_protocol.entity_get.return_value = entity

        result = await client_session_read_only.call_tool(
            "entity_get", {"entity_type": "project", "entity_id": "p-1"}
        )

        assert not result.isError
        mock_entities_protocol.entity_get.assert_called_once()


class TestEntitiesFind:
    async def test_finds_entities(
        self, client_session: ClientSession, mock_entities_protocol: AsyncMock
    ) -> None:
        entities = [
            Entity.model_construct(id="p-1", shortId=1, entityType="project"),
            Entity.model_construct(id="p-2", shortId=2, entityType="project"),
        ]
        mock_entities_protocol.entities_find.return_value = entities

        result = await client_session.call_tool(
            "entities_find",
            {"entity_type": "project", "input": "proj", "per_page": 10},
        )

        assert not result.isError
        mock_entities_protocol.entities_find.assert_called_once()
        call_args = mock_entities_protocol.entities_find.call_args
        assert call_args.args[0] == "project"
        assert call_args.kwargs["input"] == "proj"
        assert call_args.kwargs["per_page"] == 10

        content = get_tool_result_content(result)
        assert len(content) == 2
