import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import QueueNotFound

QUEUE_SCOPED_READS: list[tuple[str, str]] = [
    ("queue_get", "https://api.tracker.yandex.net/v3/queues/MISSING"),
    ("queues_get_tags", "https://api.tracker.yandex.net/v3/queues/MISSING/tags"),
    (
        "queues_get_versions",
        "https://api.tracker.yandex.net/v3/queues/MISSING/versions",
    ),
    (
        "queues_get_local_fields",
        "https://api.tracker.yandex.net/v3/queues/MISSING/localFields",
    ),
    ("queues_get_fields", "https://api.tracker.yandex.net/v3/queues/MISSING/fields"),
]


class TestQueueScopedNotFound:
    """Every queue-scoped read reports a missing queue the same way.

    A 404 from these endpoints only ever means the queue does not exist, so they
    raise QueueNotFound rather than the generic TrackerAPIError - the same rule
    the issue-scoped methods follow with IssueNotFound.
    """

    @pytest.mark.parametrize(
        ("method_name", "url"),
        QUEUE_SCOPED_READS,
        ids=[method_name for method_name, _ in QUEUE_SCOPED_READS],
    )
    async def test_raises_queue_not_found(
        self,
        tracker_client: TrackerClient,
        method_name: str,
        url: str,
    ) -> None:
        method = getattr(tracker_client, method_name)

        with aioresponses() as m:
            m.get(url, status=404)

            with pytest.raises(QueueNotFound) as exc_info:
                await method("MISSING")

            assert exc_info.value.queue_id == "MISSING"
