from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.templates import CommentTemplate, IssueTemplate
from tests.mcp.conftest import get_tool_result_content, page


class TestIssueTemplatesGetAll:
    async def test_returns_issue_templates(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        mock_templates_protocol.get_issue_templates.side_effect = [
            page(sample_issue_templates),
            page([]),
        ]

        result = await client_session.call_tool("issue_templates_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["values"]) == len(sample_issue_templates)
        assert content["values"][0]["id"] == sample_issue_templates[0].id
        assert content["values"][0]["name"] == sample_issue_templates[0].name

    async def test_returns_field_templates(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_template: IssueTemplate,
    ) -> None:
        """The prefilled field values are the point of the tool - they must survive
        serialization back to the MCP client."""
        mock_templates_protocol.get_issue_templates.side_effect = [
            page([sample_issue_template]),
            page([]),
        ]

        result = await client_session.call_tool("issue_templates_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert (
            content["values"][0]["fieldTemplates"]
            == sample_issue_template.fieldTemplates
        )

    async def test_walks_all_pages_by_default(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        """The endpoint paginates with a default of 50 items per page, so the tool
        keeps asking for pages until a short one arrives."""
        mock_templates_protocol.get_issue_templates.side_effect = [
            page(sample_issue_templates[:2]),
            page(sample_issue_templates[2:]),
            page([]),
        ]

        result = await client_session.call_tool(
            "issue_templates_get_all", {"per_page": 2}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["values"]) == len(sample_issue_templates)
        requested = [
            (call.kwargs["page"], call.kwargs["per_page"])
            for call in mock_templates_protocol.get_issue_templates.call_args_list
        ]
        # The third (empty) page is never requested: page 2 came back short.
        assert requested == [(1, 2), (2, 2)]

    async def test_returns_requested_page_only(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        mock_templates_protocol.get_issue_templates.side_effect = [
            page(sample_issue_templates[:2]),
            page([]),
        ]

        result = await client_session.call_tool(
            "issue_templates_get_all", {"page": 2, "per_page": 2}
        )

        assert not result.isError
        assert len(get_tool_result_content(result)["values"]) == 2
        mock_templates_protocol.get_issue_templates.assert_called_once()
        call_args = mock_templates_protocol.get_issue_templates.call_args
        assert call_args.kwargs["page"] == 2
        assert call_args.kwargs["per_page"] == 2

    async def test_scopes_to_queue(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_template: IssueTemplate,
    ) -> None:
        mock_templates_protocol.get_issue_templates.side_effect = [
            page([sample_issue_template]),
            page([]),
        ]

        result = await client_session.call_tool(
            "issue_templates_get_all", {"queue": "TEST"}
        )

        assert not result.isError
        call_args = mock_templates_protocol.get_issue_templates.call_args
        assert call_args.kwargs["queue"] == "TEST"

    async def test_queue_is_not_scoped_by_default(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
    ) -> None:
        mock_templates_protocol.get_issue_templates.return_value = page([])

        result = await client_session.call_tool("issue_templates_get_all", {})

        assert not result.isError
        call_args = mock_templates_protocol.get_issue_templates.call_args
        assert call_args.kwargs["queue"] is None

    async def test_filters_templates_of_restricted_queues(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        """Templates bound to a queue outside TRACKER_LIMIT_QUEUES are dropped,
        while queue-less templates stay visible."""
        mock_templates_protocol.get_issue_templates.side_effect = [
            page(sample_issue_templates),
            page([]),
        ]

        result = await client_session_with_limits.call_tool(
            "issue_templates_get_all", {}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        returned_names = {template["name"] for template in content["values"]}
        assert returned_names == {"Incident", "Personal template"}

    async def test_allows_permitted_queue_scope(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        mock_templates_protocol.get_issue_templates.side_effect = [
            page([sample_issue_templates[1]]),
            page([]),
        ]

        result = await client_session_with_limits.call_tool(
            "issue_templates_get_all", {"queue": "ALLOWED"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert {template["name"] for template in content["values"]} == {"Incident"}

    async def test_rejects_restricted_queue_scope(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_templates_get_all", {"queue": "TEST"}
        )

        assert result.isError
        mock_templates_protocol.get_issue_templates.assert_not_called()

    async def test_returns_empty_list(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
    ) -> None:
        mock_templates_protocol.get_issue_templates.return_value = page([])

        result = await client_session.call_tool("issue_templates_get_all", {})

        assert not result.isError
        assert get_tool_result_content(result)["values"] == []


class TestIssueTemplateGet:
    async def test_returns_issue_template(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_template: IssueTemplate,
    ) -> None:
        mock_templates_protocol.get_issue_template.return_value = sample_issue_template

        result = await client_session.call_tool(
            "issue_template_get", {"template_id": "1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["id"] == sample_issue_template.id
        assert content["name"] == sample_issue_template.name
        assert content["fieldTemplates"] == sample_issue_template.fieldTemplates

    async def test_passes_template_id(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_template: IssueTemplate,
    ) -> None:
        mock_templates_protocol.get_issue_template.return_value = sample_issue_template

        result = await client_session.call_tool(
            "issue_template_get", {"template_id": "42"}
        )

        assert not result.isError
        call_args = mock_templates_protocol.get_issue_template.call_args
        assert call_args[0][0] == "42"

    async def test_allows_template_of_permitted_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        mock_templates_protocol.get_issue_template.return_value = (
            sample_issue_templates[1]
        )

        result = await client_session_with_limits.call_tool(
            "issue_template_get", {"template_id": "2"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["name"] == "Incident"

    async def test_rejects_template_of_restricted_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_template: IssueTemplate,
    ) -> None:
        mock_templates_protocol.get_issue_template.return_value = sample_issue_template

        result = await client_session_with_limits.call_tool(
            "issue_template_get", {"template_id": "1"}
        )

        assert result.isError

    async def test_allows_template_without_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_issue_templates: list[IssueTemplate],
    ) -> None:
        mock_templates_protocol.get_issue_template.return_value = (
            sample_issue_templates[2]
        )

        result = await client_session_with_limits.call_tool(
            "issue_template_get", {"template_id": "3"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["name"] == "Personal template"


class TestCommentTemplatesGetAll:
    async def test_returns_comment_templates(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        mock_templates_protocol.get_comment_templates.side_effect = [
            page(sample_comment_templates),
            page([]),
        ]

        result = await client_session.call_tool("comment_templates_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content["values"]) == len(sample_comment_templates)
        assert content["values"][0]["id"] == sample_comment_templates[0].id
        assert content["values"][0]["name"] == sample_comment_templates[0].name

    async def test_returns_template_text_and_summonees(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_template: CommentTemplate,
    ) -> None:
        """The comment body and its summonees are the point of the tool - they
        must survive serialization back to the MCP client."""
        mock_templates_protocol.get_comment_templates.side_effect = [
            page([sample_comment_template]),
            page([]),
        ]

        result = await client_session.call_tool("comment_templates_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["values"][0]["template"] == sample_comment_template.template
        assert (
            content["values"][0]["description"] == sample_comment_template.description
        )
        assert content["values"][0]["summonees"][0]["display"] == "Ivan Ivanov"
        assert content["values"][0]["maillistSummonees"][0]["id"] == "duty@example.com"

    async def test_walks_all_pages_by_default(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        """The endpoint paginates with a default of 50 items per page, so the tool
        keeps asking for pages until a short one arrives."""
        mock_templates_protocol.get_comment_templates.side_effect = [
            page(sample_comment_templates[:2]),
            page(sample_comment_templates[2:]),
            page([]),
        ]

        result = await client_session.call_tool(
            "comment_templates_get_all", {"per_page": 2}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert len(content) == len(sample_comment_templates)
        requested = [
            (call.kwargs["page"], call.kwargs["per_page"])
            for call in mock_templates_protocol.get_comment_templates.call_args_list
        ]
        # The third (empty) page is never requested: page 2 came back short.
        assert requested == [(1, 2), (2, 2)]

    async def test_returns_requested_page_only(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        mock_templates_protocol.get_comment_templates.side_effect = [
            page(sample_comment_templates[:2]),
            page([]),
        ]

        result = await client_session.call_tool(
            "comment_templates_get_all", {"page": 2, "per_page": 2}
        )

        assert not result.isError
        assert len(get_tool_result_content(result)["values"]) == 2
        mock_templates_protocol.get_comment_templates.assert_called_once()
        call_args = mock_templates_protocol.get_comment_templates.call_args
        assert call_args.kwargs["page"] == 2
        assert call_args.kwargs["per_page"] == 2

    async def test_scopes_to_queue(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_template: CommentTemplate,
    ) -> None:
        mock_templates_protocol.get_comment_templates.side_effect = [
            page([sample_comment_template]),
            page([]),
        ]

        result = await client_session.call_tool(
            "comment_templates_get_all", {"queue": "TEST"}
        )

        assert not result.isError
        call_args = mock_templates_protocol.get_comment_templates.call_args
        assert call_args.kwargs["queue"] == "TEST"

    async def test_queue_is_not_scoped_by_default(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
    ) -> None:
        mock_templates_protocol.get_comment_templates.return_value = page([])

        result = await client_session.call_tool("comment_templates_get_all", {})

        assert not result.isError
        call_args = mock_templates_protocol.get_comment_templates.call_args
        assert call_args.kwargs["queue"] is None

    async def test_filters_templates_of_restricted_queues(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        """Templates bound to a queue outside TRACKER_LIMIT_QUEUES are dropped,
        while queue-less templates stay visible."""
        mock_templates_protocol.get_comment_templates.side_effect = [
            page(sample_comment_templates),
            page([]),
        ]

        result = await client_session_with_limits.call_tool(
            "comment_templates_get_all", {}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        returned_names = {template["name"] for template in content["values"]}
        assert returned_names == {"Escalation", "Personal reply"}

    async def test_allows_permitted_queue_scope(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        mock_templates_protocol.get_comment_templates.side_effect = [
            page([sample_comment_templates[1]]),
            page([]),
        ]

        result = await client_session_with_limits.call_tool(
            "comment_templates_get_all", {"queue": "ALLOWED"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert {template["name"] for template in content["values"]} == {"Escalation"}

    async def test_rejects_restricted_queue_scope(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "comment_templates_get_all", {"queue": "TEST"}
        )

        assert result.isError
        mock_templates_protocol.get_comment_templates.assert_not_called()

    async def test_returns_empty_list(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
    ) -> None:
        mock_templates_protocol.get_comment_templates.return_value = page([])

        result = await client_session.call_tool("comment_templates_get_all", {})

        assert not result.isError
        assert get_tool_result_content(result)["values"] == []


class TestCommentTemplateGet:
    async def test_returns_comment_template(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_template: CommentTemplate,
    ) -> None:
        mock_templates_protocol.get_comment_template.return_value = (
            sample_comment_template
        )

        result = await client_session.call_tool(
            "comment_template_get", {"template_id": "1"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["id"] == sample_comment_template.id
        assert content["name"] == sample_comment_template.name
        assert content["template"] == sample_comment_template.template

    async def test_passes_template_id(
        self,
        client_session: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_template: CommentTemplate,
    ) -> None:
        mock_templates_protocol.get_comment_template.return_value = (
            sample_comment_template
        )

        result = await client_session.call_tool(
            "comment_template_get", {"template_id": "42"}
        )

        assert not result.isError
        call_args = mock_templates_protocol.get_comment_template.call_args
        assert call_args[0][0] == "42"

    async def test_allows_template_of_permitted_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        mock_templates_protocol.get_comment_template.return_value = (
            sample_comment_templates[1]
        )

        result = await client_session_with_limits.call_tool(
            "comment_template_get", {"template_id": "2"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["name"] == "Escalation"

    async def test_rejects_template_of_restricted_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_template: CommentTemplate,
    ) -> None:
        mock_templates_protocol.get_comment_template.return_value = (
            sample_comment_template
        )

        result = await client_session_with_limits.call_tool(
            "comment_template_get", {"template_id": "1"}
        )

        assert result.isError

    async def test_allows_template_without_queue(
        self,
        client_session_with_limits: ClientSession,
        mock_templates_protocol: AsyncMock,
        sample_comment_templates: list[CommentTemplate],
    ) -> None:
        mock_templates_protocol.get_comment_template.return_value = (
            sample_comment_templates[2]
        )

        result = await client_session_with_limits.call_tool(
            "comment_template_get", {"template_id": "3"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["name"] == "Personal reply"
