"""Access control helpers for MCP tools."""

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import ComponentNotFound, IssueNotFound
from mcp_tracker.tracker.proto.types.components import Component


def _is_read_only_queue(settings: Settings, queue: str) -> bool:
    """Return True if the given queue is configured as read-only."""
    return bool(
        settings.tracker_read_only_queues
        and queue.upper() in settings.tracker_read_only_queues
    )


def is_queue_allowed(settings: Settings, queue: str) -> bool:
    """Return True if the queue is reachable under ``TRACKER_LIMIT_QUEUES``.

    The raising `check_*_access` helpers below and the tools that filter whole
    listings share this one definition of the allow-list. Both settings hold a
    set of upper-cased keys (see `Settings.decode_queue_keys`), so the casing of
    the configuration does not matter and the check stays a hash lookup - which
    is what a listing tool does per row.
    """
    return (
        not settings.tracker_limit_queues
        or queue.upper() in settings.tracker_limit_queues
    )


def _check_scoped_queue(
    settings: Settings, queue: str, *, not_found: Exception, write: bool
) -> None:
    """The one check behind every `check_*_access` helper.

    Raises ``not_found`` for a queue outside ``TRACKER_LIMIT_QUEUES`` and, for
    a ``write``, rejects a queue listed in ``TRACKER_READ_ONLY_QUEUES``.
    """
    if not is_queue_allowed(settings, queue):
        raise not_found
    if write and _is_read_only_queue(settings, queue):
        raise TrackerError(
            f"Queue `{queue}` is read-only; write operations are not allowed."
        )


def check_issue_access(
    settings: Settings, issue_id: str, *, write: bool = False
) -> None:
    """Check access to an issue through the queue its key names."""
    queue = issue_id.split("-")[0]
    _check_scoped_queue(settings, queue, not_found=IssueNotFound(issue_id), write=write)


def check_queue_access(
    settings: Settings, queue_id: str, *, write: bool = False
) -> None:
    """Check access to a queue named by the caller."""
    _check_scoped_queue(
        settings,
        queue_id,
        not_found=TrackerError(f"Queue `{queue_id}` not found or not allowed."),
        write=write,
    )


def queue_checks_needed(settings: Settings, *, write: bool) -> bool:
    """Whether a tool has to learn an entity's queue before acting on it.

    True when ``TRACKER_LIMIT_QUEUES`` is set, or - for a write - when
    ``TRACKER_READ_ONLY_QUEUES`` is. A tool whose argument names no queue (a
    component id, say) needs an extra read to find the queue to check, and
    on an unrestricted server that read buys nothing.
    """
    if settings.tracker_limit_queues:
        return True
    return write and bool(settings.tracker_read_only_queues)


def check_component_access(
    settings: Settings, component: Component, *, write: bool = False
) -> None:
    """Check access to a component through the queue it belongs to.

    A no-op unless `queue_checks_needed`. A component whose response carries
    no queue key cannot be checked, so under a restriction it is refused
    rather than let through. One in a queue outside ``TRACKER_LIMIT_QUEUES``
    raises `ComponentNotFound`, one in a read-only queue is rejected for a
    write with the queue named, as `check_queue_access` does.
    """
    if not queue_checks_needed(settings, write=write):
        return

    queue_key = component.queue.key if component.queue is not None else None
    if queue_key is None:
        raise TrackerError(
            f"Component `{component.id}` names no queue, so its access cannot be "
            f"checked against the queue restrictions; refusing."
        )

    # The caller knows the component by id alone, and the key came from the
    # API: a queue the allow-list hides must not be named back at them.
    _check_scoped_queue(
        settings, queue_key, not_found=ComponentNotFound(component.id), write=write
    )
