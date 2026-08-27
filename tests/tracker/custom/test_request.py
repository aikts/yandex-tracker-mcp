"""The funnel every Tracker request goes through.

`TrackerClient._request` is the one place that builds the headers, translates a
timeout, turns a non-2xx into `TrackerAPIError` and maps the statuses that have
a meaning of their own onto a domain error. It used to be sixty copies of those
lines, one per method, and the copies drifted: `TrackerAPITimeout` reached the
caller from `boards_list` alone, every other method answered a timeout with an
empty message. These tests cover the funnel itself - that the sixty callers
still behave is what the rest of the suite says.
"""

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    IssueNotFound,
    IssueVersionConflict,
    TrackerAPIError,
    TrackerAPITimeout,
)
from tests.aioresponses_utils import RequestCapture

URL = "https://api.tracker.yandex.net/v3/thing"
PATH = "v3/thing"

VERBS = ["GET", "POST", "PATCH", "DELETE"]


class TestRequestForwarding:
    @pytest.mark.parametrize("verb", VERBS)
    async def test_sends_the_verb_url_and_auth_headers(
        self, tracker_client: TrackerClient, verb: str
    ) -> None:
        capture = RequestCapture(payload={"ok": True})

        with aioresponses() as m:
            m.add(URL, method=verb, callback=capture.callback)

            async with tracker_client._request(verb, PATH, auth=None) as response:
                assert response.status == 200

        capture.assert_called_once()
        assert capture.last_request.url.path == "/v3/thing"
        capture.last_request.assert_headers(
            {"Authorization": "OAuth test-token", "X-Org-ID": "test-org"}
        )

    async def test_forwards_params_and_json_body(
        self, tracker_client: TrackerClient
    ) -> None:
        capture = RequestCapture(payload={"ok": True})

        with aioresponses() as m:
            m.post(f"{URL}?perPage=25", callback=capture.callback)

            async with tracker_client._request(
                "POST",
                PATH,
                auth=None,
                params={"perPage": 25},
                json={"query": "Queue: TEST"},
            ) as response:
                assert response.status == 200

        capture.last_request.assert_param("perPage", 25)
        capture.last_request.assert_json_body({"query": "Queue: TEST"})


class TestRequestTimeout:
    async def test_a_timeout_names_the_request_and_the_knob(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(URL, exception=TimeoutError())

            with pytest.raises(TrackerAPITimeout) as exc_info:
                async with tracker_client._request("GET", PATH, auth=None):
                    pass  # pragma: no cover - the request never gets this far

        error = exc_info.value
        assert error.method == "GET"
        assert error.url == PATH
        assert error.timeout == tracker_client._timeout
        message = str(error)
        assert message, "a timeout must not reach the caller as an empty message"
        assert PATH in message
        assert "TRACKER_API_TIMEOUT" in message

    async def test_a_timeout_reading_the_body_is_translated_too(
        self, tracker_client: TrackerClient
    ) -> None:
        """The body is read inside the caller's `async with`.

        A response that starts arriving and then stalls raises from
        `response.read()`, which is the caller's block rather than the request
        itself; `@asynccontextmanager` throws that back in at the `yield`, where
        the same handler catches it.
        """
        with aioresponses() as m:
            m.get(URL, payload={"ok": True})

            with pytest.raises(TrackerAPITimeout) as exc_info:
                async with tracker_client._request("GET", PATH, auth=None):
                    raise TimeoutError()

        assert str(exc_info.value)
        assert exc_info.value.url == PATH


class TestRequestStatusMapping:
    async def test_404_raises_the_given_error(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(URL, status=404, payload={"errorMessages": ["Не найдено."]})

            with pytest.raises(IssueNotFound) as exc_info:
                async with tracker_client._request(
                    "GET", PATH, auth=None, not_found=IssueNotFound("TEST-1")
                ):
                    pass  # pragma: no cover - the status is raised before this

        assert exc_info.value.issue_id == "TEST-1"

    async def test_404_without_a_mapping_carries_the_api_explanation(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(URL, status=404, payload={"errorMessages": ["Не найдено."]})

            with pytest.raises(TrackerAPIError) as exc_info:
                async with tracker_client._request("GET", PATH, auth=None):
                    pass  # pragma: no cover - the status is raised before this

        assert exc_info.value.status == 404
        assert "Не найдено." in str(exc_info.value)

    async def test_409_raises_the_given_error(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.patch(URL, status=409, payload={"errorMessages": ["Конфликт версий."]})

            with pytest.raises(IssueVersionConflict) as exc_info:
                async with tracker_client._request(
                    "PATCH",
                    PATH,
                    auth=None,
                    conflict=IssueVersionConflict("TEST-1", 3),
                ):
                    pass  # pragma: no cover - the status is raised before this

        assert "TEST-1" in str(exc_info.value)

    async def test_409_without_a_mapping_is_an_api_error(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.patch(URL, status=409, payload={"errorMessages": ["Конфликт версий."]})

            with pytest.raises(TrackerAPIError) as exc_info:
                async with tracker_client._request("PATCH", PATH, auth=None):
                    pass  # pragma: no cover - the status is raised before this

        assert exc_info.value.status == 409

    @pytest.mark.parametrize("status", [400, 403, 422, 500])
    async def test_any_other_failure_is_an_api_error(
        self, tracker_client: TrackerClient, status: int
    ) -> None:
        with aioresponses() as m:
            m.get(URL, status=status, payload={"errorMessages": ["Нет доступа."]})

            with pytest.raises(TrackerAPIError) as exc_info:
                async with tracker_client._request(
                    "GET", PATH, auth=None, not_found=IssueNotFound("TEST-1")
                ):
                    pass  # pragma: no cover - the status is raised before this

        assert exc_info.value.status == status
        assert "Нет доступа." in str(exc_info.value)


class TestAllowStatuses:
    """`user_get` answers a 404 with `None`, so it asks for the status itself."""

    async def test_an_allowed_status_reaches_the_caller(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(URL, status=404, payload={"errorMessages": ["Не найдено."]})

            async with tracker_client._request(
                "GET",
                PATH,
                auth=None,
                not_found=IssueNotFound("TEST-1"),
                allow_statuses=(404,),
            ) as response:
                assert response.status == 404

    async def test_it_allows_only_the_status_it_names(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(URL, status=500, payload={"errorMessages": ["Ошибка."]})

            with pytest.raises(TrackerAPIError):
                async with tracker_client._request(
                    "GET", PATH, auth=None, allow_statuses=(404,)
                ):
                    pass  # pragma: no cover - the status is raised before this


class TestRead:
    async def test_returns_the_body(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(URL, payload={"key": "TEST-1"})

            body = await tracker_client._read("GET", PATH, auth=None)

        assert body == b'{"key": "TEST-1"}'

    async def test_it_maps_a_status_like_request_does(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.delete(URL, status=404, payload={"errorMessages": ["Не найдено."]})

            with pytest.raises(IssueNotFound):
                await tracker_client._read(
                    "DELETE", PATH, auth=None, not_found=IssueNotFound("TEST-1")
                )

    async def test_it_translates_a_timeout_like_request_does(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(URL, exception=TimeoutError())

            with pytest.raises(TrackerAPITimeout):
                await tracker_client._read("GET", PATH, auth=None)
