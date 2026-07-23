"""Access control helpers for MCP tools."""

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import IssueNotFound


def _is_read_only_queue(settings: Settings, queue: str) -> bool:
    """Return True if the given queue is configured as read-only."""
    return bool(
        settings.tracker_read_only_queues and queue in settings.tracker_read_only_queues
    )


def check_issue_access(
    settings: Settings, issue_id: str, *, write: bool = False
) -> None:
    """Check if access to the issue is allowed based on queue restrictions.

    When ``write`` is True, the target queue is additionally validated against
    the per-queue read-only allow-list (``TRACKER_READ_ONLY_QUEUES``); mutations
    on read-only queues are rejected.
    """
    queue = issue_id.split("-")[0]
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise IssueNotFound(issue_id)
    if write and _is_read_only_queue(settings, queue):
        raise TrackerError(
            f"Queue `{queue}` is read-only; write operations are not allowed."
        )


def check_queue_access(
    settings: Settings, queue_id: str, *, write: bool = False
) -> None:
    """Check if access to the queue is allowed based on queue restrictions.

    When ``write`` is True, the queue is additionally validated against the
    per-queue read-only allow-list (``TRACKER_READ_ONLY_QUEUES``); mutations on
    read-only queues are rejected.
    """
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")
    if write and _is_read_only_queue(settings, queue_id):
        raise TrackerError(
            f"Queue `{queue_id}` is read-only; write operations are not allowed."
        )
