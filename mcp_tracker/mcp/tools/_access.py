"""Access control helpers for MCP tools."""

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import IssueNotFound


def check_issue_access(settings: Settings, issue_id: str) -> None:
    """Check if access to the issue is allowed based on queue restrictions."""
    queue = issue_id.split("-")[0]
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise IssueNotFound(issue_id)


def check_queue_access(settings: Settings, queue_id: str) -> None:
    """Check if access to the queue is allowed based on queue restrictions."""
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")
