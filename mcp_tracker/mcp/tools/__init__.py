"""MCP tools package for Yandex Tracker.

This package organizes MCP tools by category:
- queue.py: Queue-related tools (read-only)
- field.py: Global field and metadata tools (read-only)
- issue_read.py: Issue read-only tools
- issue_write.py: Issue write tools (conditional on read-only mode)
- user.py: User-related tools (read-only)
"""

from typing import Any

from mcp.server import FastMCP

from mcp_tracker.mcp.tools.field import register_field_tools
from mcp_tracker.mcp.tools.issue_read import register_issue_read_tools
from mcp_tracker.mcp.tools.issue_write import register_issue_write_tools
from mcp_tracker.mcp.tools.queue import register_queue_tools
from mcp_tracker.mcp.tools.user import register_user_tools
from mcp_tracker.settings import Settings


def register_all_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register all MCP tools based on settings.

    Args:
        settings: Application settings. If tracker_read_only is True,
            write tools will not be registered.
        mcp: FastMCP server instance.
    """
    # Always register read-only tools
    register_queue_tools(settings, mcp)
    register_field_tools(settings, mcp)
    register_issue_read_tools(settings, mcp)
    register_user_tools(settings, mcp)

    # Only register write tools if not in read-only mode
    if not settings.tracker_read_only:
        register_issue_write_tools(settings, mcp)


__all__ = ["register_all_tools"]
