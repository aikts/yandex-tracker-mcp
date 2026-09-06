from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import ComponentNotFound

URL = "https://api.tracker.yandex.net/v3/components/99999"

COMPONENT_SCOPED_CALLS: list[tuple[str, str, str, dict[str, Any]]] = [
    ("component_get", "GET", URL, {}),
    ("component_update", "PATCH", f"{URL}?version=1", {"version": 1, "name": "X"}),
    ("component_delete", "DELETE", URL, {}),
]


class TestComponentScopedNotFound:
    """Every component-scoped method reports an unknown id the same way.

    A 404 from `v3/components/{id}` only ever means the component does not
    exist - deleting twice answers it too - so they raise ComponentNotFound
    rather than the generic TrackerAPIError, the rule the queue-scoped methods
    follow with QueueNotFound.
    """

    @pytest.mark.parametrize(
        ("method_name", "verb", "url", "kwargs"),
        COMPONENT_SCOPED_CALLS,
        ids=[method_name for method_name, *_ in COMPONENT_SCOPED_CALLS],
    )
    async def test_raises_component_not_found(
        self,
        tracker_client: TrackerClient,
        method_name: str,
        verb: str,
        url: str,
        kwargs: dict[str, Any],
    ) -> None:
        method = getattr(tracker_client, method_name)

        with aioresponses() as m:
            m.add(
                url,
                method=verb,
                status=404,
                payload={"errorMessages": ["Компонент не существует."]},
            )

            with pytest.raises(ComponentNotFound) as exc_info:
                await method(99999, **kwargs)

        assert exc_info.value.component_id == 99999
        assert "99999" in str(exc_info.value)
