from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from tests.mcp.conftest import get_tool_result_content


class TestGetGlobalFields:
    async def test_returns_global_fields(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_global_fields: list[GlobalField],
    ) -> None:
        mock_fields_protocol.get_global_fields.return_value = sample_global_fields

        result = await client_session.call_tool("get_global_fields", {})

        assert not result.isError
        mock_fields_protocol.get_global_fields.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_global_fields)
        assert content[0]["id"] == sample_global_fields[0].id
        assert content[0]["name"] == sample_global_fields[0].name


class TestGetStatuses:
    async def test_returns_statuses(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_statuses: list[Status],
    ) -> None:
        mock_fields_protocol.get_statuses.return_value = sample_statuses

        result = await client_session.call_tool("get_statuses", {})

        assert not result.isError
        mock_fields_protocol.get_statuses.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_statuses)
        assert content[0]["key"] == sample_statuses[0].key
        assert content[0]["name"] == sample_statuses[0].name


class TestGetIssueTypes:
    async def test_returns_issue_types(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_issue_types: list[IssueType],
    ) -> None:
        mock_fields_protocol.get_issue_types.return_value = sample_issue_types

        result = await client_session.call_tool("get_issue_types", {})

        assert not result.isError
        mock_fields_protocol.get_issue_types.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_issue_types)
        assert content[0]["key"] == sample_issue_types[0].key
        assert content[0]["name"] == sample_issue_types[0].name


class TestGetPriorities:
    async def test_returns_priorities(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_priorities: list[Priority],
    ) -> None:
        mock_fields_protocol.get_priorities.return_value = sample_priorities

        result = await client_session.call_tool("get_priorities", {})

        assert not result.isError
        mock_fields_protocol.get_priorities.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_priorities)
        assert content[0]["key"] == sample_priorities[0].key
        assert content[0]["name"] == sample_priorities[0].name


class TestGetResolutions:
    async def test_returns_resolutions(
        self,
        client_session: ClientSession,
        mock_fields_protocol: AsyncMock,
        sample_resolutions: list[Resolution],
    ) -> None:
        mock_fields_protocol.get_resolutions.return_value = sample_resolutions

        result = await client_session.call_tool("get_resolutions", {})

        assert not result.isError
        mock_fields_protocol.get_resolutions.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_resolutions)
        assert content[0]["key"] == sample_resolutions[0].key
        assert content[0]["name"] == sample_resolutions[0].name
