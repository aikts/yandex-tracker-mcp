from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import ProjectEntity
from mcp_tracker.tracker.proto.types.inputs import ProjectPortfolioLinkInput
from tests.mcp.conftest import get_tool_result_content


class TestProjectCreate:
    async def test_creates_project(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_create.return_value = sample_project

        result = await client_session.call_tool(
            "project_create",
            {"summary": "New Project", "team_access": True},
        )

        assert not result.isError
        mock_entities_protocol.project_create.assert_called_once_with(
            summary="New Project",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=True,
            links=None,
            fields=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_project.id

    async def test_passes_links_and_fields(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_create.return_value = sample_project

        result = await client_session.call_tool(
            "project_create",
            {
                "summary": "New Project",
                "links": [{"relationship": "works towards", "entity": "goal-1"}],
                "fields": ["summary", "entityStatus"],
            },
        )

        assert not result.isError
        call_kwargs = mock_entities_protocol.project_create.call_args.kwargs
        assert call_kwargs["links"] == [
            ProjectPortfolioLinkInput(relationship="works towards", entity="goal-1")
        ]
        assert call_kwargs["fields"] == ["summary", "entityStatus"]

    async def test_rejects_unknown_link_relationship(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        result = await client_session.call_tool(
            "project_create",
            {
                "summary": "New Project",
                "links": [{"relationship": "is supported by", "entity": "goal-1"}],
            },
        )

        assert result.isError
        mock_entities_protocol.project_create.assert_not_called()

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_create", {"summary": "New Project"}
        )

        assert result.isError


class TestProjectUpdate:
    async def test_updates_project(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_update.return_value = sample_project

        result = await client_session.call_tool(
            "project_update",
            {"entity_id": "abc123", "summary": "Renamed", "version": 5},
        )

        assert not result.isError
        mock_entities_protocol.project_update.assert_called_once_with(
            "abc123",
            summary="Renamed",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            comment=None,
            version=5,
            links=None,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_update", {"entity_id": "abc123"}
        )

        assert result.isError


class TestProjectDelete:
    async def test_deletes_project(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        mock_entities_protocol.project_delete.return_value = None

        result = await client_session.call_tool(
            "project_delete", {"entity_id": "abc123", "with_board": True}
        )

        assert not result.isError
        mock_entities_protocol.project_delete.assert_called_once_with(
            "abc123", with_board=True, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_delete", {"entity_id": "abc123"}
        )

        assert result.isError
