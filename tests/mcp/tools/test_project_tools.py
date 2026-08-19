from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import ProjectEntity, ProjectSearchResult
from mcp_tracker.tracker.proto.types.issues import CommentsPage, IssueComment
from tests.mcp.conftest import get_tool_result_content


class TestProjectGet:
    async def test_returns_project(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_get.return_value = sample_project

        result = await client_session.call_tool("project_get", {"entity_id": "abc123"})

        assert not result.isError
        mock_entities_protocol.project_get.assert_called_once()
        content = get_tool_result_content(result)
        assert content["id"] == sample_project.id
        assert sample_project.fields is not None
        assert content["fields"]["summary"] == sample_project.fields.summary

    async def test_passes_entity_id_and_fields(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_get.return_value = sample_project

        await client_session.call_tool(
            "project_get",
            {"entity_id": "abc123", "fields": ["summary", "entityStatus"]},
        )

        call_kwargs = mock_entities_protocol.project_get.call_args.kwargs
        assert call_kwargs["fields"] == ["summary", "entityStatus"]
        mock_entities_protocol.project_get.assert_called_once_with(
            "abc123", fields=["summary", "entityStatus"], auth=YandexAuth()
        )

    async def test_omitted_fields_passed_as_none(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_project: ProjectEntity,
    ) -> None:
        mock_entities_protocol.project_get.return_value = sample_project

        await client_session.call_tool("project_get", {"entity_id": "abc123"})

        call_kwargs = mock_entities_protocol.project_get.call_args.kwargs
        assert call_kwargs["fields"] is None


class TestProjectFind:
    async def test_returns_projects(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_projects: ProjectSearchResult,
    ) -> None:
        mock_entities_protocol.project_find.return_value = sample_projects

        result = await client_session.call_tool("project_find", {})

        assert not result.isError
        mock_entities_protocol.project_find.assert_called_once()
        content = get_tool_result_content(result)
        assert content["hits"] == sample_projects.hits
        assert len(content["values"]) == len(sample_projects.values)

    async def test_passes_search_parameters(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_projects: ProjectSearchResult,
    ) -> None:
        mock_entities_protocol.project_find.return_value = sample_projects

        await client_session.call_tool(
            "project_find",
            {
                "input": "test",
                "filter": {"entityStatus": "in_progress"},
                "order_by": "summary",
                "order_asc": True,
                "root_only": True,
                "page": 2,
                "per_page": 25,
            },
        )

        mock_entities_protocol.project_find.assert_called_once_with(
            input="test",
            filter={"entityStatus": "in_progress"},
            order_by="summary",
            order_asc=True,
            root_only=True,
            per_page=25,
            page=2,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_optional_parameters_omitted(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_projects: ProjectSearchResult,
    ) -> None:
        mock_entities_protocol.project_find.return_value = sample_projects

        await client_session.call_tool("project_find", {})

        call_kwargs = mock_entities_protocol.project_find.call_args.kwargs
        assert call_kwargs["input"] is None
        assert call_kwargs["filter"] is None
        assert call_kwargs["order_by"] is None
        assert call_kwargs["order_asc"] is None
        assert call_kwargs["root_only"] is None


class TestProjectGetComments:
    async def test_returns_comments(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_entities_protocol.project_get_comments.return_value = CommentsPage(
            comments=sample_comments, next_cursor="99"
        )

        result = await client_session.call_tool(
            "project_get_comments", {"entity_id": "abc123"}
        )

        assert not result.isError
        mock_entities_protocol.project_get_comments.assert_called_once_with(
            "abc123", per_page=50, cursor=None, auth=YandexAuth()
        )
        content = get_tool_result_content(result)
        assert content["next_cursor"] == "99"
        assert len(content["comments"]) == len(sample_comments)
        assert content["comments"][0]["text"] == sample_comments[0].text

    async def test_passes_pagination_params(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_entities_protocol.project_get_comments.return_value = CommentsPage(
            comments=sample_comments
        )

        result = await client_session.call_tool(
            "project_get_comments",
            {"entity_id": "abc123", "per_page": 10, "cursor": "42"},
        )

        assert not result.isError
        mock_entities_protocol.project_get_comments.assert_called_once_with(
            "abc123", per_page=10, cursor="42", auth=YandexAuth()
        )
        assert get_tool_result_content(result)["next_cursor"] is None
