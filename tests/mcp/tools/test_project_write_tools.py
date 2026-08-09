from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import ProjectEntity
from mcp_tracker.tracker.proto.types.inputs import (
    EntityChecklistItemUpdateInput,
    ProjectPortfolioLinkInput,
)
from mcp_tracker.tracker.proto.types.issues import IssueComment
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


class TestProjectAddComment:
    async def test_adds_comment(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comment: IssueComment,
    ) -> None:
        mock_entities_protocol.project_add_comment.return_value = sample_comment

        result = await client_session.call_tool(
            "project_add_comment",
            {"entity_id": "abc123", "text": "Hello", "summonees": ["user123"]},
        )

        assert not result.isError
        mock_entities_protocol.project_add_comment.assert_called_once_with(
            "abc123",
            text="Hello",
            summonees=["user123"],
            maillist_summonees=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_comment.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_add_comment", {"entity_id": "abc123", "text": "Hello"}
        )

        assert result.isError


class TestProjectUpdateComment:
    async def test_updates_comment(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comment: IssueComment,
    ) -> None:
        mock_entities_protocol.project_update_comment.return_value = sample_comment

        result = await client_session.call_tool(
            "project_update_comment",
            {"entity_id": "abc123", "comment_id": 1, "text": "Updated"},
        )

        assert not result.isError
        mock_entities_protocol.project_update_comment.assert_called_once_with(
            "abc123",
            1,
            text="Updated",
            summonees=None,
            maillist_summonees=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_comment.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_update_comment",
            {"entity_id": "abc123", "comment_id": 1, "text": "Updated"},
        )

        assert result.isError


class TestProjectDeleteComment:
    async def test_deletes_comment(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
    ) -> None:
        mock_entities_protocol.project_delete_comment.return_value = None

        result = await client_session.call_tool(
            "project_delete_comment", {"entity_id": "abc123", "comment_id": 1}
        )

        assert not result.isError
        mock_entities_protocol.project_delete_comment.assert_called_once_with(
            "abc123", 1, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_delete_comment", {"entity_id": "abc123", "comment_id": 1}
        )

        assert result.isError


class TestProjectAddChecklistItem:
    async def test_adds_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_add_checklist_item.return_value = sample_project

        result = await client_session.call_tool(
            "project_add_checklist_item",
            {"entity_id": "abc123", "text": "Do the thing", "checked": True},
        )

        assert not result.isError
        mock_entities_protocol.project_add_checklist_item.assert_called_once_with(
            "abc123",
            text="Do the thing",
            checked=True,
            assignee=None,
            deadline=None,
            fields=None,
            auth=YandexAuth(),
        )
        content = get_tool_result_content(result)
        assert content["id"] == sample_project.id

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_add_checklist_item",
            {"entity_id": "abc123", "text": "Do the thing"},
        )

        assert result.isError


class TestProjectUpdateChecklistItem:
    async def test_updates_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_update_checklist_item.return_value = (
            sample_project
        )

        result = await client_session.call_tool(
            "project_update_checklist_item",
            {"entity_id": "abc123", "checklist_item_id": "item1", "checked": True},
        )

        assert not result.isError
        mock_entities_protocol.project_update_checklist_item.assert_called_once_with(
            "abc123",
            "item1",
            text=None,
            checked=True,
            assignee=None,
            deadline=None,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_update_checklist_item",
            {"entity_id": "abc123", "checklist_item_id": "item1", "checked": True},
        )

        assert result.isError


class TestProjectMoveChecklistItem:
    async def test_moves_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_move_checklist_item.return_value = sample_project

        result = await client_session.call_tool(
            "project_move_checklist_item",
            {
                "entity_id": "abc123",
                "checklist_item_id": "item1",
                "before": "item0",
            },
        )

        assert not result.isError
        mock_entities_protocol.project_move_checklist_item.assert_called_once_with(
            "abc123",
            "item1",
            before="item0",
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_move_checklist_item",
            {"entity_id": "abc123", "checklist_item_id": "item1", "before": "item0"},
        )

        assert result.isError


class TestProjectDeleteChecklistItem:
    async def test_deletes_checklist_item(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_delete_checklist_item.return_value = (
            sample_project
        )

        result = await client_session.call_tool(
            "project_delete_checklist_item",
            {"entity_id": "abc123", "checklist_item_id": "item1"},
        )

        assert not result.isError
        mock_entities_protocol.project_delete_checklist_item.assert_called_once_with(
            "abc123",
            "item1",
            fields=None,
            auth=YandexAuth(),
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_delete_checklist_item",
            {"entity_id": "abc123", "checklist_item_id": "item1"},
        )

        assert result.isError


class TestProjectUpdateChecklist:
    async def test_updates_checklist(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_update_checklist.return_value = sample_project

        result = await client_session.call_tool(
            "project_update_checklist",
            {
                "entity_id": "abc123",
                "items": [{"id": "item1", "text": "Do the thing", "checked": True}],
            },
        )

        assert not result.isError
        call_kwargs = mock_entities_protocol.project_update_checklist.call_args.kwargs
        assert call_kwargs["items"] == [
            EntityChecklistItemUpdateInput(
                id="item1", text="Do the thing", checked=True
            )
        ]
        assert call_kwargs["fields"] is None

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_update_checklist",
            {
                "entity_id": "abc123",
                "items": [{"id": "item1", "text": "Do the thing"}],
            },
        )

        assert result.isError


class TestProjectDeleteChecklist:
    async def test_deletes_checklist(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_delete_checklist.return_value = sample_project

        result = await client_session.call_tool(
            "project_delete_checklist", {"entity_id": "abc123"}
        )

        assert not result.isError
        mock_entities_protocol.project_delete_checklist.assert_called_once_with(
            "abc123", fields=None, auth=YandexAuth()
        )

    async def test_read_only_mode_tool_not_registered(
        self,
        client_session_read_only: ClientSession,
    ) -> None:
        result = await client_session_read_only.call_tool(
            "project_delete_checklist", {"entity_id": "abc123"}
        )

        assert result.isError
