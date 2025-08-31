from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import IssueTransition
from tests.aioresponses_utils import RequestCapture


@pytest.fixture
def sample_transition_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions/start",
        "id": "start",
        "display": "Start Progress",
        "to": {
            "self": "https://api.tracker.yandex.net/v3/statuses/2",
            "id": "2",
            "key": "inProgress",
            "display": "In Progress",
        },
    }


@pytest.fixture
def sample_done_transition_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions/close",
        "id": "close",
        "display": "Close Issue",
        "to": {
            "self": "https://api.tracker.yandex.net/v3/statuses/3",
            "id": "3",
            "key": "closed",
            "display": "Closed",
        },
    }


@pytest.fixture
def sample_statuses_data() -> list[dict[str, Any]]:
    return [
        {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "version": 1,
            "key": "open",
            "name": "Open",
            "order": 1,
            "type": "new",
        },
        {
            "self": "https://api.tracker.yandex.net/v3/statuses/2",
            "id": "2",
            "version": 1,
            "key": "inProgress",
            "name": "In Progress",
            "order": 2,
            "type": "inProgress",
        },
        {
            "self": "https://api.tracker.yandex.net/v3/statuses/3",
            "id": "3",
            "version": 1,
            "key": "closed",
            "name": "Closed",
            "order": 3,
            "type": "done",
        },
    ]


class TestIssueGetTransitions:
    async def test_success(
        self, tracker_client: TrackerClient, sample_transition_data: dict[str, Any]
    ) -> None:
        transitions_response = [sample_transition_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )

            result = await tracker_client.issue_get_transitions("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueTransition)
            assert result[0].id == "start"
            assert result[0].display == "Start Progress"
            assert result[0].to is not None
            assert result[0].to.key == "inProgress"

    async def test_with_auth(
        self,
        tracker_client: TrackerClient,
        sample_transition_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        transitions_response = [sample_transition_data]
        capture = RequestCapture(payload=transitions_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                callback=capture.callback,
            )

            result = await tracker_client.issue_get_transitions(
                "TEST-123", auth=yandex_auth
            )

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/NOTFOUND-123/transitions",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_transitions("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_multiple_transitions(
        self,
        tracker_client: TrackerClient,
        sample_transition_data: dict[str, Any],
        sample_done_transition_data: dict[str, Any],
    ) -> None:
        transitions_response = [sample_transition_data, sample_done_transition_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )

            result = await tracker_client.issue_get_transitions("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(t, IssueTransition) for t in result)
            assert result[0].id == "start"
            assert result[1].id == "close"


class TestIssueExecuteTransition:
    async def test_success_minimal(
        self, tracker_client: TrackerClient, sample_transition_data: dict[str, Any]
    ) -> None:
        transitions_response = [sample_transition_data]
        capture = RequestCapture(payload=transitions_response)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/start/_execute",
                callback=capture.callback,
            )

            result = await tracker_client.issue_execute_transition("TEST-123", "start")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueTransition)

        capture.assert_called_once()
        capture.last_request.assert_json_body({})

    async def test_success_with_comment(
        self, tracker_client: TrackerClient, sample_transition_data: dict[str, Any]
    ) -> None:
        transitions_response = [sample_transition_data]
        capture = RequestCapture(payload=transitions_response)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/start/_execute",
                callback=capture.callback,
            )

            result = await tracker_client.issue_execute_transition(
                "TEST-123",
                "start",
                comment="Starting work on this issue",
            )

            assert isinstance(result, list)

        capture.assert_called_once()
        capture.last_request.assert_json_field("comment", "Starting work on this issue")

    async def test_success_with_fields(
        self, tracker_client: TrackerClient, sample_transition_data: dict[str, Any]
    ) -> None:
        transitions_response = [sample_transition_data]
        capture = RequestCapture(payload=transitions_response)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/start/_execute",
                callback=capture.callback,
            )

            result = await tracker_client.issue_execute_transition(
                "TEST-123",
                "start",
                fields={"resolution": "fixed", "customField": "value"},
            )

            assert isinstance(result, list)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["resolution"] == "fixed"
        assert body["customField"] == "value"

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_transition_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        transitions_response = [sample_transition_data]
        capture = RequestCapture(payload=transitions_response)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/start/_execute",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issue_execute_transition(
                "TEST-123",
                "start",
                auth=yandex_auth,
            )

            assert isinstance(result, list)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/transitions/start/_execute",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_execute_transition("NOTFOUND-123", "start")

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueClose:
    async def test_success(
        self,
        tracker_client: TrackerClient,
        sample_transition_data: dict[str, Any],
        sample_done_transition_data: dict[str, Any],
        sample_statuses_data: list[dict[str, Any]],
    ) -> None:
        transitions_response = [sample_transition_data, sample_done_transition_data]
        execute_capture = RequestCapture(payload=[sample_done_transition_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )
            m.get(
                "https://api.tracker.yandex.net/v3/statuses",
                payload=sample_statuses_data,
            )
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/close/_execute",
                callback=execute_capture.callback,
            )

            result = await tracker_client.issue_close("TEST-123", "fixed")

            assert isinstance(result, list)
            assert len(result) == 1

        execute_capture.assert_called_once()
        body = execute_capture.last_request.get_json_body()
        assert body["resolution"] == "fixed"

    async def test_success_with_comment(
        self,
        tracker_client: TrackerClient,
        sample_transition_data: dict[str, Any],
        sample_done_transition_data: dict[str, Any],
        sample_statuses_data: list[dict[str, Any]],
    ) -> None:
        transitions_response = [sample_transition_data, sample_done_transition_data]
        execute_capture = RequestCapture(payload=[sample_done_transition_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )
            m.get(
                "https://api.tracker.yandex.net/v3/statuses",
                payload=sample_statuses_data,
            )
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/close/_execute",
                callback=execute_capture.callback,
            )

            result = await tracker_client.issue_close(
                "TEST-123",
                "fixed",
                comment="Closing this issue",
            )

            assert isinstance(result, list)

        execute_capture.assert_called_once()
        body = execute_capture.last_request.get_json_body()
        assert body["comment"] == "Closing this issue"
        assert body["resolution"] == "fixed"

    async def test_success_with_fields(
        self,
        tracker_client: TrackerClient,
        sample_transition_data: dict[str, Any],
        sample_done_transition_data: dict[str, Any],
        sample_statuses_data: list[dict[str, Any]],
    ) -> None:
        transitions_response = [sample_transition_data, sample_done_transition_data]
        execute_capture = RequestCapture(payload=[sample_done_transition_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )
            m.get(
                "https://api.tracker.yandex.net/v3/statuses",
                payload=sample_statuses_data,
            )
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/close/_execute",
                callback=execute_capture.callback,
            )

            result = await tracker_client.issue_close(
                "TEST-123",
                "fixed",
                fields={"customField": "value"},
            )

            assert isinstance(result, list)

        execute_capture.assert_called_once()
        body = execute_capture.last_request.get_json_body()
        assert body["resolution"] == "fixed"
        assert body["customField"] == "value"

    async def test_no_done_transition_raises_error(
        self,
        tracker_client: TrackerClient,
        sample_transition_data: dict[str, Any],
    ) -> None:
        # Only provide a transition to "inProgress" status (not "done" type)
        transitions_response = [sample_transition_data]
        statuses_response = [
            {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "version": 1,
                "key": "open",
                "name": "Open",
                "order": 1,
                "type": "new",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/statuses/2",
                "id": "2",
                "version": 1,
                "key": "inProgress",
                "name": "In Progress",
                "order": 2,
                "type": "inProgress",
            },
        ]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )
            m.get(
                "https://api.tracker.yandex.net/v3/statuses",
                payload=statuses_response,
            )

            with pytest.raises(ValueError) as exc_info:
                await tracker_client.issue_close("TEST-123", "fixed")

            assert "No transition to a 'done' status found" in str(exc_info.value)

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_transition_data: dict[str, Any],
        sample_done_transition_data: dict[str, Any],
        sample_statuses_data: list[dict[str, Any]],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        transitions_response = [sample_transition_data, sample_done_transition_data]
        execute_capture = RequestCapture(payload=[sample_done_transition_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v2/issues/TEST-123/transitions",
                payload=transitions_response,
            )
            m.get(
                "https://api.tracker.yandex.net/v3/statuses",
                payload=sample_statuses_data,
            )
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/transitions/close/_execute",
                callback=execute_capture.callback,
            )

            result = await tracker_client_no_org.issue_close(
                "TEST-123",
                "fixed",
                auth=yandex_auth_cloud,
            )

            assert isinstance(result, list)

        execute_capture.assert_called_once()
        execute_capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
