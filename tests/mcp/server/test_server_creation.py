import pytest
from mcp import Client

from tests.test_release_metadata import VERSION

# Read-only tool names (35 tools) - always registered
READ_ONLY_TOOL_NAMES = [
    # Queue tools (6)
    "queues_get_all",
    "queue_get_tags",
    "queue_get_versions",
    "queue_get_components",
    "queue_get_fields",
    "queue_get_metadata",
    # Component tools (1)
    "component_get",
    # Field tools (10)
    "get_global_fields",
    "get_statuses",
    "get_issue_types",
    "get_priorities",
    "get_resolutions",
    "issue_templates_get_all",
    "issue_template_get",
    "comment_templates_get_all",
    "comment_template_get",
    "issue_get_url",
    # Board tools (4)
    "boards_get_all",
    "board_get",
    "board_get_columns",
    "board_get_sprints",
    # Issue read tools (10)
    "issue_get",
    "issue_get_comments",
    "issue_get_links",
    "issues_find",
    "issues_count",
    "issue_get_worklogs",
    "issue_get_attachments",
    "issue_get_checklist",
    "issue_get_transitions",
    "issue_get_changelog",
    # User tools (4)
    "users_get_all",
    "users_search",
    "user_get",
    "user_get_current",
]

# Entity read tools - registered only when TRACKER_ENTITIES_ENABLED is set
ENTITY_READ_ONLY_TOOL_NAMES = [
    # Project entity tools (3)
    "project_get",
    "project_find",
    "project_get_comments",
    # Portfolio entity tools (3)
    "portfolio_get",
    "portfolio_find",
    "portfolio_get_comments",
    # Goal entity tools (3)
    "goal_get",
    "goal_find",
    "goal_get_comments",
]

# Write tool names - only registered when not in read-only mode
WRITE_TOOL_NAMES = [
    "queue_create_version",
    "component_create",
    "component_update",
    "component_delete",
    "issue_execute_transition",
    "issue_close",
    "issue_create",
    "issue_update",
    "issue_add_worklog",
    "issue_update_worklog",
    "issue_delete_worklog",
    "issue_add_comment",
    "issue_update_comment",
    "issue_delete_comment",
    "issue_add_link",
    "issue_delete_link",
    "issue_move",
    "issue_add_checklist_items",
    "issue_update_checklist_item",
    "issue_delete_checklist_item",
]

# Entity write tools - require both write mode and TRACKER_ENTITIES_ENABLED
ENTITY_WRITE_TOOL_NAMES = [
    "project_create",
    "project_update",
    "project_delete",
    "project_add_comment",
    "project_update_comment",
    "project_delete_comment",
    "project_add_checklist_item",
    "project_update_checklist_item",
    "project_move_checklist_item",
    "project_delete_checklist_item",
    "project_update_checklist",
    "project_delete_checklist",
    "portfolio_create",
    "portfolio_update",
    "portfolio_delete",
    "portfolio_add_comment",
    "portfolio_update_comment",
    "portfolio_delete_comment",
    "portfolio_add_checklist_item",
    "portfolio_update_checklist_item",
    "portfolio_move_checklist_item",
    "portfolio_delete_checklist_item",
    "portfolio_update_checklist",
    "portfolio_delete_checklist",
    "goal_create",
    "goal_update",
    "goal_delete",
    "goal_add_comment",
    "goal_update_comment",
    "goal_delete_comment",
]

ALL_READ_ONLY_TOOL_NAMES = READ_ONLY_TOOL_NAMES + ENTITY_READ_ONLY_TOOL_NAMES
ALL_WRITE_TOOL_NAMES = WRITE_TOOL_NAMES + ENTITY_WRITE_TOOL_NAMES

# All tool names that should be registered in normal mode (entity tools enabled)
EXPECTED_TOOL_NAMES = ALL_READ_ONLY_TOOL_NAMES + ALL_WRITE_TOOL_NAMES


class TestToolRegistration:
    @pytest.mark.parametrize("tool_name", EXPECTED_TOOL_NAMES)
    async def test_tool_is_registered(
        self,
        client_session: Client,
        tool_name: str,
    ) -> None:
        result = await client_session.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert tool_name in tool_names, f"Tool '{tool_name}' is not registered"


class TestReadOnlyModeToolRegistration:
    """Test tool registration in read-only mode."""

    @pytest.mark.parametrize("tool_name", ALL_READ_ONLY_TOOL_NAMES)
    async def test_read_only_tools_are_registered(
        self,
        client_session_read_only: Client,
        tool_name: str,
    ) -> None:
        """Read-only tools should be registered in read-only mode."""
        result = await client_session_read_only.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert tool_name in tool_names, (
            f"Read-only tool '{tool_name}' should be registered in read-only mode"
        )

    @pytest.mark.parametrize("tool_name", ALL_WRITE_TOOL_NAMES)
    async def test_write_tools_are_not_registered(
        self,
        client_session_read_only: Client,
        tool_name: str,
    ) -> None:
        """Write tools should NOT be registered in read-only mode."""
        result = await client_session_read_only.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert tool_name not in tool_names, (
            f"Write tool '{tool_name}' should NOT be registered in read-only mode"
        )

    async def test_correct_tool_count_in_read_only_mode(
        self,
        client_session_read_only: Client,
    ) -> None:
        """Read-only mode should have only read-only tools."""
        result = await client_session_read_only.list_tools()

        assert len(result.tools) == len(ALL_READ_ONLY_TOOL_NAMES), (
            f"Expected {len(ALL_READ_ONLY_TOOL_NAMES)} tools in read-only mode, "
            f"got {len(result.tools)}"
        )

    async def test_correct_tool_count_in_normal_mode(
        self,
        client_session: Client,
    ) -> None:
        """Normal mode should have all tools (read-only + write)."""
        result = await client_session.list_tools()

        assert len(result.tools) == len(EXPECTED_TOOL_NAMES), (
            f"Expected {len(EXPECTED_TOOL_NAMES)} tools in normal mode, "
            f"got {len(result.tools)}"
        )


class TestEntityToolRegistration:
    """Entity tools are opt-in via TRACKER_ENTITIES_ENABLED (default off)."""

    @pytest.mark.parametrize(
        "tool_name", ENTITY_READ_ONLY_TOOL_NAMES + ENTITY_WRITE_TOOL_NAMES
    )
    async def test_entity_tools_are_not_registered_by_default(
        self,
        client_session_entities_disabled: Client,
        tool_name: str,
    ) -> None:
        result = await client_session_entities_disabled.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert tool_name not in tool_names, (
            f"Entity tool '{tool_name}' should NOT be registered when "
            f"tracker_entities_enabled is False"
        )

    @pytest.mark.parametrize("tool_name", READ_ONLY_TOOL_NAMES + WRITE_TOOL_NAMES)
    async def test_non_entity_tools_stay_registered(
        self,
        client_session_entities_disabled: Client,
        tool_name: str,
    ) -> None:
        result = await client_session_entities_disabled.list_tools()

        tool_names = [tool.name for tool in result.tools]
        assert tool_name in tool_names

    async def test_correct_tool_count_with_entities_disabled(
        self,
        client_session_entities_disabled: Client,
    ) -> None:
        result = await client_session_entities_disabled.list_tools()

        expected = len(READ_ONLY_TOOL_NAMES) + len(WRITE_TOOL_NAMES)
        assert len(result.tools) == expected, (
            f"Expected {expected} tools with entity tools disabled, "
            f"got {len(result.tools)}"
        )


class TestResourceRegistration:
    async def test_configuration_resource_is_registered(
        self,
        client_session: Client,
    ) -> None:
        """The configuration resource is a template (optional query variables),
        so it is listed under `resources/templates/list`, not `resources/list`."""
        result = await client_session.list_resource_templates()

        templates = [t.uri_template for t in result.resource_templates]
        assert "tracker-mcp://configuration{?cloudOrgId,orgId}" in templates


class TestServerConfiguration:
    async def test_server_has_correct_name(
        self,
        client_session: Client,
    ) -> None:
        # `Client.__aenter__` already negotiated the connection; on a modern
        # (2026-07-28) connection the identity arrives as a `_meta` stamp,
        # which is optional - so `server_info` is `None` for an anonymous
        # server, and the first assert is what tells that apart from a rename.
        assert client_session.server_info is not None
        assert client_session.server_info.name == "Yandex Tracker MCP Server"

    async def test_server_reports_the_package_version(
        self,
        client_session: Client,
    ) -> None:
        """`serverInfo.version` is read from the installed package metadata and
        is deliberately empty when that is missing - so a distribution name
        drifting from `pyproject.toml` would report "" with every test green."""
        assert client_session.server_info is not None
        assert client_session.server_info.version == VERSION

    async def test_server_has_instructions(
        self,
        client_session: Client,
    ) -> None:
        instructions = client_session.instructions

        assert instructions is not None
        assert len(instructions) > 0
