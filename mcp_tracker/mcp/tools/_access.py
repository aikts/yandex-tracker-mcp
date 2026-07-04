"""Access control helpers for MCP tools."""

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.components import Component


def check_issue_access(settings: Settings, issue_id: str) -> None:
    """Check if access to the issue is allowed based on queue restrictions."""
    queue = issue_id.split("-")[0]
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise IssueNotFound(issue_id)


def check_queue_access(settings: Settings, queue_id: str) -> None:
    """Check if access to the queue is allowed based on queue restrictions."""
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")


def check_component_access(settings: Settings, component: Component) -> None:
    """Check if access to the component is allowed based on queue restrictions."""
    if not settings.tracker_limit_queues:
        return

    queue_key = component.queue.key if component.queue is not None else None
    if queue_key is None:
        raise TrackerError(f"Component `{component.name}` queue is unknown; access denied.")

    check_queue_access(settings, queue_key)
