import re
from typing import Any, TypedDict

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


class MoveFlags(TypedDict, total=False):
    notify: bool
    notify_author: bool
    move_all_fields: bool
    initial_status: bool


@pytest.fixture
def moved_issue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/NEWQUEUE-42",
        "id": "593cd211ef7e8a33********",
        "key": "NEWQUEUE-42",
        "version": 2,
        "summary": "Test issue",
        "status": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Open",
        },
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/NEWQUEUE",
            "id": "10",
            "key": "NEWQUEUE",
            "display": "New Queue",
        },
    }


class TestIssueMove:
    async def test_success(
        self, tracker_client: TrackerClient, moved_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/_move?queue=NEWQUEUE",
                callback=capture.callback,
            )

            result = await tracker_client.issue_move("TEST-123", "NEWQUEUE")

            assert isinstance(result, Issue)
            assert result.key == "NEWQUEUE-42"

        capture.assert_called_once()

    async def test_sends_queue_as_query_param(
        self, tracker_client: TrackerClient, moved_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/_move?queue=TARGET",
                callback=capture.callback,
            )

            await tracker_client.issue_move("TEST-123", "TARGET")

        capture.assert_called_once()
        assert capture.last_request.url.query_string == "queue=TARGET"

    @pytest.mark.parametrize(
        ("kwargs", "expected_params"),
        [
            ({}, {"queue": "NEWQUEUE"}),
            ({"notify": True}, {"queue": "NEWQUEUE"}),
            ({"notify": False}, {"queue": "NEWQUEUE", "notify": "false"}),
            ({"notify_author": False}, {"queue": "NEWQUEUE"}),
            (
                {"notify_author": True},
                {"queue": "NEWQUEUE", "notifyAuthor": "true"},
            ),
            ({"move_all_fields": False}, {"queue": "NEWQUEUE"}),
            (
                {"move_all_fields": True},
                {"queue": "NEWQUEUE", "moveAllFields": "true"},
            ),
            ({"initial_status": False}, {"queue": "NEWQUEUE"}),
            (
                {"initial_status": True},
                {"queue": "NEWQUEUE", "initialStatus": "true"},
            ),
            (
                {
                    "notify": False,
                    "notify_author": True,
                    "move_all_fields": True,
                    "initial_status": True,
                },
                {
                    "queue": "NEWQUEUE",
                    "notify": "false",
                    "notifyAuthor": "true",
                    "moveAllFields": "true",
                    "initialStatus": "true",
                },
            ),
        ],
    )
    async def test_sends_optional_flags_as_query_params(
        self,
        tracker_client: TrackerClient,
        moved_issue_data: dict[str, Any],
        kwargs: MoveFlags,
        expected_params: dict[str, str],
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    r"^https://api\.tracker\.yandex\.net/v3/issues/TEST-123/_move"
                ),
                callback=capture.callback,
            )

            await tracker_client.issue_move("TEST-123", "NEWQUEUE", **kwargs)

        capture.assert_called_once()
        assert dict(capture.last_request.url.query) == expected_params

    async def test_not_found_raises_issue_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        from mcp_tracker.tracker.custom.errors import IssueNotFound

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/MISSING-1/_move?queue=NEWQUEUE",
                status=404,
            )

            with pytest.raises(IssueNotFound):
                await tracker_client.issue_move("MISSING-1", "NEWQUEUE")

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        moved_issue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=moved_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/_move?queue=NEWQUEUE",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issue_move(
                "TEST-123", "NEWQUEUE", auth=yandex_auth_cloud
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
