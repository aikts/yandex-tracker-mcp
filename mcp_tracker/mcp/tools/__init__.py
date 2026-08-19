"""MCP tools package for Yandex Tracker.

This package organizes MCP tools by category:
- queue.py: Queue-related tools (read-only)
- queue_write.py: Queue write tools (conditional on read-only mode)
- field.py: Global field and metadata tools (read-only)
- template.py: Issue and comment template tools (read-only)
- issue_read.py: Issue read-only tools
- issue_write.py: Issue write tools (conditional on read-only mode)
- user.py: User-related tools (read-only)
- project.py: Project entity tools (read-only)
- project_write.py: Project entity write tools (conditional on read-only mode)
- portfolio.py: Portfolio entity tools (read-only)
- portfolio_write.py: Portfolio entity write tools (conditional on read-only mode)
- goal.py: Goal entity tools (read-only)
- goal_write.py: Goal entity write tools (conditional on read-only mode)
"""

from typing import Any

from mcp.server import FastMCP

from mcp_tracker.mcp.tools.field import register_field_tools
from mcp_tracker.mcp.tools.goal import register_goal_tools
from mcp_tracker.mcp.tools.goal_write import register_goal_write_tools
from mcp_tracker.mcp.tools.issue_read import register_issue_read_tools
from mcp_tracker.mcp.tools.issue_write import register_issue_write_tools
from mcp_tracker.mcp.tools.portfolio import register_portfolio_tools
from mcp_tracker.mcp.tools.portfolio_write import register_portfolio_write_tools
from mcp_tracker.mcp.tools.project import register_project_tools
from mcp_tracker.mcp.tools.project_write import register_project_write_tools
from mcp_tracker.mcp.tools.queue import register_queue_tools
from mcp_tracker.mcp.tools.queue_write import register_queue_write_tools
from mcp_tracker.mcp.tools.template import register_template_tools
from mcp_tracker.mcp.tools.user import register_user_tools
from mcp_tracker.settings import Settings


def register_all_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register all MCP tools based on settings.

    Args:
        settings: Application settings. If tracker_read_only is True,
            write tools will not be registered. Project/portfolio/goal tools
            are registered only if tracker_entities_enabled is True.
        mcp: FastMCP server instance.
    """
    # Always register read-only tools
    register_queue_tools(settings, mcp)
    register_field_tools(settings, mcp)
    register_template_tools(settings, mcp)
    register_issue_read_tools(settings, mcp)
    register_user_tools(settings, mcp)

    if settings.tracker_entities_enabled:
        register_project_tools(settings, mcp)
        register_portfolio_tools(settings, mcp)
        register_goal_tools(settings, mcp)

    # Only register write tools if not in read-only mode
    if not settings.tracker_read_only:
        register_queue_write_tools(settings, mcp)
        register_issue_write_tools(settings, mcp)

        if settings.tracker_entities_enabled:
            register_project_write_tools(settings, mcp)
            register_portfolio_write_tools(settings, mcp)
            register_goal_write_tools(settings, mcp)


__all__ = ["register_all_tools"]
