import pytest
from mcp.client.session import ClientSession

# All tool names that should be registered
EXPECTED_TOOL_NAMES = [
    "queues_get_all",
    "queue_get_tags",
    "queue_get_versions",
    "queue_get_fields",
    "queue_get_metadata",
    "get_global_fields",
    "get_statuses",
    "get_issue_types",
    "get_priorities",
    "get_resolutions",
    "issue_get_url",
    "issue_get",
    "issue_get_comments",
    "issue_get_links",
    "issues_find",
    "issues_count",
    "issue_get_worklogs",
    "issue_get_attachments",
    "issue_get_checklist",
    "issue_get_transitions",
    "issue_execute_transition",
    "issue_close",
    "issue_create",
    "issue_update",
    "users_get_all",
    "users_search",
    "user_get",
    "user_get_current",
]


class TestToolRegistration:
    @pytest.mark.parametrize("tool_name", EXPECTED_TOOL_NAMES)
    async def test_tool_is_registered(
        self,
        client_session: ClientSession,
        tool_name: str,
    ) -> None:
        result = await client_session.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert tool_name in tool_names, f"Tool '{tool_name}' is not registered"


class TestResourceRegistration:
    async def test_configuration_resource_is_registered(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.list_resources()

        resource_uris = [str(r.uri) for r in result.resources]
        assert "tracker-mcp://configuration" in resource_uris


class TestServerConfiguration:
    async def test_server_has_correct_name(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.initialize()

        assert result.serverInfo.name == "Yandex Tracker MCP Server"

    async def test_server_has_instructions(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.initialize()

        assert result.instructions is not None
        assert len(result.instructions) > 0
