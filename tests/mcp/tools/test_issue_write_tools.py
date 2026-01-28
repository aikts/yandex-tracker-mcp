from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.issues import Issue, IssueTransition, Worklog
from tests.mcp.conftest import get_tool_result_content


class TestIssueExecuteTransition:
    async def test_executes_transition(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_execute_transition.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_execute_transition",
            {"issue_id": "TEST-123", "transition_id": "start_progress"},
        )

        assert not result.isError
        mock_issues_protocol.issue_execute_transition.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_transitions)
        assert content[0]["id"] == sample_transitions[0].id

    async def test_with_comment(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_execute_transition.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_execute_transition",
            {
                "issue_id": "TEST-123",
                "transition_id": "start_progress",
                "comment": "Starting work on this issue",
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_execute_transition.call_args.kwargs
        assert call_kwargs["comment"] == "Starting work on this issue"
        content = get_tool_result_content(result)
        assert len(content) == len(sample_transitions)

    async def test_with_fields(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_execute_transition.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_execute_transition",
            {
                "issue_id": "TEST-123",
                "transition_id": "resolve",
                "fields": {"resolution": "fixed"},
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_execute_transition.call_args.kwargs
        assert call_kwargs["fields"] == {"resolution": "fixed"}
        content = get_tool_result_content(result)
        assert isinstance(content, list)

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_execute_transition",
            {"issue_id": "RESTRICTED-123", "transition_id": "start_progress"},
        )

        assert result.isError
        mock_issues_protocol.issue_execute_transition.assert_not_called()


class TestIssueClose:
    async def test_closes_issue(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_close.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_close",
            {"issue_id": "TEST-123", "resolution_id": "fixed"},
        )

        assert not result.isError
        mock_issues_protocol.issue_close.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_transitions)

    async def test_with_comment(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_close.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_close",
            {
                "issue_id": "TEST-123",
                "resolution_id": "fixed",
                "comment": "Issue resolved successfully",
            },
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_close.call_args.kwargs
        assert call_kwargs["comment"] == "Issue resolved successfully"
        content = get_tool_result_content(result)
        assert len(content) == len(sample_transitions)

    async def test_with_additional_fields(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_close.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_close",
            {
                "issue_id": "TEST-123",
                "resolution_id": "fixed",
                "fields": {"assignee": "user123"},
            },
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)


class TestIssueCreate:
    async def test_creates_issue(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_create.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_create",
            {"queue": "TEST", "summary": "New test issue"},
        )

        assert not result.isError
        mock_issues_protocol.issue_create.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["key"] == sample_issue.key
        assert content["summary"] == sample_issue.summary

    async def test_with_all_parameters(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_create.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_create",
            {
                "queue": "TEST",
                "summary": "New test issue",
                "description": "Detailed description",
                "type": 1,
                "assignee": "user123",
                "priority": "normal",
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_create.assert_called_once()
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key

    async def test_with_custom_fields(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_create.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_create",
            {
                "queue": "TEST",
                "summary": "New test issue",
                "fields": {"customField": "custom value"},
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_create.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_create",
            {"queue": "RESTRICTED", "summary": "New issue"},
        )

        assert result.isError
        mock_issues_protocol.issue_create.assert_not_called()


class TestIssueUpdate:
    async def test_updates_summary(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_update.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_update",
            {"issue_id": "TEST-123", "summary": "Updated summary"},
        )

        assert not result.isError
        mock_issues_protocol.issue_update.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["key"] == sample_issue.key

    async def test_updates_description(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_update.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_update",
            {"issue_id": "TEST-123", "description": "Updated description"},
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_update.call_args.kwargs
        assert call_kwargs["description"] == "Updated description"
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key

    async def test_updates_multiple_fields(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_update.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_update",
            {
                "issue_id": "TEST-123",
                "summary": "Updated summary",
                "description": "Updated description",
                "tags": ["new-tag"],
            },
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["key"] == sample_issue.key

    async def test_with_version_for_optimistic_locking(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_update.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_update",
            {"issue_id": "TEST-123", "summary": "Updated summary", "version": 5},
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issue_update.call_args.kwargs
        assert call_kwargs["version"] == 5
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_update",
            {"issue_id": "RESTRICTED-123", "summary": "Updated summary"},
        )

        assert result.isError
        mock_issues_protocol.issue_update.assert_not_called()


class TestIssueAddWorklog:
    async def test_adds_worklog(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklog: Worklog,
    ) -> None:
        mock_issues_protocol.issue_add_worklog.return_value = sample_worklog

        result = await client_session.call_tool(
            "issue_add_worklog",
            {"issue_id": "TEST-123", "duration": "PT1H", "comment": "Worked on task"},
        )

        assert not result.isError
        mock_issues_protocol.issue_add_worklog.assert_called_once()
        call_kwargs = mock_issues_protocol.issue_add_worklog.call_args.kwargs
        assert call_kwargs["duration"] == "PT1H"
        assert call_kwargs["comment"] == "Worked on task"
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["id"] == sample_worklog.id

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_add_worklog",
            {"issue_id": "RESTRICTED-123", "duration": "PT15M"},
        )

        assert result.isError
        mock_issues_protocol.issue_add_worklog.assert_not_called()


class TestIssueUpdateWorklog:
    async def test_updates_worklog(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklog: Worklog,
    ) -> None:
        mock_issues_protocol.issue_update_worklog.return_value = sample_worklog

        result = await client_session.call_tool(
            "issue_update_worklog",
            {
                "issue_id": "TEST-123",
                "worklog_id": 10,
                "duration": "PT2H",
                "comment": "Updated",
            },
        )

        assert not result.isError
        mock_issues_protocol.issue_update_worklog.assert_called_once()
        call_kwargs = mock_issues_protocol.issue_update_worklog.call_args.kwargs
        assert call_kwargs["duration"] == "PT2H"
        assert call_kwargs["comment"] == "Updated"
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["id"] == sample_worklog.id

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_update_worklog",
            {"issue_id": "RESTRICTED-123", "worklog_id": 10, "comment": "x"},
        )

        assert result.isError
        mock_issues_protocol.issue_update_worklog.assert_not_called()


class TestIssueDeleteWorklog:
    async def test_deletes_worklog(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issue_delete_worklog.return_value = None

        result = await client_session.call_tool(
            "issue_delete_worklog",
            {"issue_id": "TEST-123", "worklog_id": 10},
        )

        assert not result.isError
        mock_issues_protocol.issue_delete_worklog.assert_called_once()
        call_args = mock_issues_protocol.issue_delete_worklog.call_args
        # Сигнатура: issue_delete_worklog(issue_id, worklog_id, *, auth=...)
        assert call_args.args[0] == "TEST-123"
        assert call_args.args[1] == 10

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_delete_worklog",
            {"issue_id": "RESTRICTED-123", "worklog_id": 10},
        )

        assert result.isError
        mock_issues_protocol.issue_delete_worklog.assert_not_called()
