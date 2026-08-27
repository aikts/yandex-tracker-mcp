"""Guard: the server instructions must not name tools or arguments that do not exist.

The instructions are the first thing an agent reads about this server, and they
drifted behind the tools once already - they described a read-only server long
after the write tools landed. A stale tool name there sends agents looking for
something that is not registered.
"""

import re
from typing import Any

import pytest
from mcp.server import FastMCP
from mcp.server.fastmcp.tools import Tool

from mcp_tracker.mcp.params import instructions

# Backticked names in the instructions that are arguments, fields or literals
# rather than tools.
NON_TOOL_NAMES = frozenset(
    {
        "page",
        "per_page",
        "cursor",
        "next_cursor",
        "fields",
        "version",
        "summonees",
        "maillistSummonees",
        "boards",
        "queue",
        "@login",
        "text",
        "hits",
        "pages",
        "comment",
        "links",
        "project",
        "shortId",
        "parent_entity",
        # A literal queue key used as an example, not a tool.
        "SOMEPROJECT",
    }
)


def _quoted_names() -> set[str]:
    return set(re.findall(r"`([A-Za-z_@][A-Za-z_]*)`", instructions))


class TestInstructions:
    @pytest.fixture
    def tool_names(self, mcp_server: FastMCP[Any]) -> set[str]:
        return {tool.name for tool in mcp_server._tool_manager.list_tools()}

    def test_every_named_tool_exists(self, tool_names: set[str]) -> None:
        named = _quoted_names() - NON_TOOL_NAMES
        assert named, "no tool names quoted in the instructions - the sweep is vacuous"
        assert named <= tool_names, (
            f"instructions name tools that are not registered: "
            f"{sorted(named - tool_names)}"
        )

    @pytest.mark.parametrize(
        ("tool_name", "argument"),
        [
            ("issue_update", "version"),
            ("issue_add_comment", "summonees"),
            ("issue_update_comment", "summonees"),
            ("issues_find", "fields"),
            ("queues_get_all", "fields"),
            ("boards_get_all", "fields"),
            ("boards_get_all", "queue"),
            ("board_get", "fields"),
            ("board_get_sprints", "fields"),
            ("issue_get_changelog", "cursor"),
        ],
    )
    def test_arguments_the_instructions_promise_exist(
        self, mcp_server: FastMCP[Any], tool_name: str, argument: str
    ) -> None:
        tools: list[Tool] = mcp_server._tool_manager.list_tools()
        tool = next(t for t in tools if t.name == tool_name)

        assert argument in (tool.parameters or {}).get("properties", {})

    def test_write_capability_is_mentioned(self) -> None:
        """The instructions described a read-only server long after writes landed."""
        assert "Create and edit issues" in instructions
