import datetime
import re
from typing import Any

import pytest
from aiohttp import ClientResponseError
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import ChangelogPage
from tests.aioresponses_utils import RequestCapture

CHANGELOG_URL = "https://api.tracker.yandex.net/v3/issues/TEST-123/changelog"
# Matches the changelog endpoint regardless of query string (aioresponses requires
# the registered query to match exactly, so use a regex when capturing arbitrary params).
CHANGELOG_URL_RE = re.compile(
    r"https://api\.tracker\.yandex\.net/v3/issues/TEST-123/changelog(\?.*)?$"
)


@pytest.fixture
def sample_changelog_entry() -> dict[str, Any]:
    return {
        "id": "5f2c0000000000000000abcd",
        "self": f"{CHANGELOG_URL}/5f2c0000000000000000abcd",
        "issue": {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
            "id": "issue123",
            "key": "TEST-123",
            "display": "Test issue summary",
        },
        "updatedAt": "2023-01-02T10:30:00.000+0000",
        "updatedBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "type": "IssueWorkflow",
        "transport": "front",
        "fields": [
            {
                "field": {
                    "self": "https://api.tracker.yandex.net/v3/fields/status",
                    "id": "status",
                    "display": "Status",
                },
                "from": {"id": "1", "key": "open", "display": "Open"},
                "to": {"id": "2", "key": "inProgress", "display": "In Progress"},
            }
        ],
    }


class TestIssueGetChangelog:
    async def test_success(
        self, tracker_client: TrackerClient, sample_changelog_entry: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                f"{CHANGELOG_URL}?perPage=50",
                payload=[sample_changelog_entry],
            )

            result = await tracker_client.issue_get_changelog("TEST-123")

        assert isinstance(result, ChangelogPage)
        assert result.next_cursor is None
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.id == "5f2c0000000000000000abcd"
        assert entry.type == "IssueWorkflow"
        assert entry.updated_by is not None
        assert entry.updated_by.display == "Test User"
        # updatedAt (ms + +0000 offset) must parse into a tz-aware datetime
        assert entry.updated_at == datetime.datetime(
            2023, 1, 2, 10, 30, tzinfo=datetime.timezone.utc
        )
        assert entry.fields is not None
        change = entry.fields[0]
        assert change.field is not None
        assert change.field.id == "status"
        # field display must be preserved, not silently dropped
        assert change.field.display == "Status"
        assert change.from_ == {"id": "1", "key": "open", "display": "Open"}
        assert change.to == {"id": "2", "key": "inProgress", "display": "In Progress"}

    async def test_empty_changelog(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(f"{CHANGELOG_URL}?perPage=50", payload=[])

            result = await tracker_client.issue_get_changelog("TEST-123")

        assert isinstance(result, ChangelogPage)
        assert result.entries == []
        assert result.next_cursor is None

    async def test_comment_and_trigger_payload_survives(
        self, tracker_client: TrackerClient, sample_changelog_entry: dict[str, Any]
    ) -> None:
        # A comment-type change delivers its payload via the top-level `comments`
        # key (not inside `fields`); executedTriggers and any other documented
        # top-level keys must not be silently dropped.
        entry = {
            **sample_changelog_entry,
            "type": "IssueCommentAdded",
            "fields": [],
            "comments": {
                "added": [
                    {"self": "https://api/c", "id": 98765, "display": "Looks good"}
                ]
            },
            "executedTriggers": [
                {
                    "trigger": {
                        "self": "https://api/t",
                        "id": 7,
                        "display": "Auto-assign",
                    },
                    "success": True,
                    "message": "ok",
                }
            ],
            # an unmodeled top-level key (e.g. worklog change) must pass through
            "worklog": {"added": [{"id": 42}]},
        }
        with aioresponses() as m:
            m.get(f"{CHANGELOG_URL}?perPage=50", payload=[entry])

            result = await tracker_client.issue_get_changelog("TEST-123")

        change = result.entries[0]
        assert change.comments is not None
        assert change.comments.added is not None
        assert change.comments.added[0].id == 98765
        assert change.comments.added[0].display == "Looks good"
        assert change.executed_triggers is not None
        trigger = change.executed_triggers[0]
        assert trigger.success is True
        assert trigger.message == "ok"
        assert trigger.trigger is not None
        assert trigger.trigger.display == "Auto-assign"
        # unmodeled top-level keys survive via extra="allow"
        assert change.model_dump(by_alias=True)["worklog"] == {"added": [{"id": 42}]}

    async def test_next_cursor_parsed_from_link_header(
        self, tracker_client: TrackerClient, sample_changelog_entry: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                f"{CHANGELOG_URL}?perPage=50",
                payload=[sample_changelog_entry],
                headers={
                    "Link": f'<{CHANGELOG_URL}?id=next-cursor-id&perPage=50>; rel="next"'
                },
            )

            result = await tracker_client.issue_get_changelog("TEST-123")

        assert result.next_cursor == "next-cursor-id"

    async def test_next_link_without_id_yields_no_cursor(
        self, tracker_client: TrackerClient, sample_changelog_entry: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                f"{CHANGELOG_URL}?perPage=50",
                payload=[sample_changelog_entry],
                headers={"Link": f'<{CHANGELOG_URL}?perPage=50>; rel="next"'},
            )

            result = await tracker_client.issue_get_changelog("TEST-123")

        # rel="next" present but no `id` query param -> cursor must stay None,
        # never the string "None"
        assert result.next_cursor is None

    async def test_second_page_uses_cursor(
        self, tracker_client: TrackerClient, sample_changelog_entry: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=[sample_changelog_entry])

        with aioresponses() as m:
            m.get(
                f"{CHANGELOG_URL}?perPage=50&id=next-cursor-id",
                callback=capture.callback,
            )

            result = await tracker_client.issue_get_changelog(
                "TEST-123", cursor="next-cursor-id"
            )

        assert len(result.entries) == 1
        # no Link header on the last page -> pagination terminates
        assert result.next_cursor is None
        capture.assert_called_once()
        capture.last_request.assert_param("id", "next-cursor-id")

    @pytest.mark.parametrize(
        ("from_value", "to_value"),
        [
            pytest.param("Old summary", "New summary", id="string"),
            pytest.param(["a", "b"], ["a", "b", "c"], id="array"),
            pytest.param(None, {"id": "user456", "display": "Other"}, id="null-from"),
        ],
    )
    async def test_from_to_arbitrary_shapes(
        self,
        tracker_client: TrackerClient,
        sample_changelog_entry: dict[str, Any],
        from_value: Any,
        to_value: Any,
    ) -> None:
        entry = {
            **sample_changelog_entry,
            "fields": [
                {
                    "field": {"id": "summary", "display": "Summary"},
                    "from": from_value,
                    "to": to_value,
                }
            ],
        }
        with aioresponses() as m:
            m.get(f"{CHANGELOG_URL}?perPage=50", payload=[entry])

            result = await tracker_client.issue_get_changelog("TEST-123")

        fields = result.entries[0].fields
        assert fields is not None
        change = fields[0]
        assert change.from_ == from_value
        assert change.to == to_value

    @pytest.mark.parametrize(
        ("kwargs", "expected_params"),
        [
            pytest.param({"per_page": 10}, {"perPage": 10}, id="per-page"),
            pytest.param({"cursor": "abc"}, {"perPage": 50, "id": "abc"}, id="cursor"),
            pytest.param(
                {"field": "status"},
                {"perPage": 50, "field": "status"},
                id="field",
            ),
            pytest.param(
                {"type": "IssueWorkflow"},
                {"perPage": 50, "type": "IssueWorkflow"},
                id="type",
            ),
        ],
    )
    async def test_passes_each_param(
        self,
        tracker_client: TrackerClient,
        sample_changelog_entry: dict[str, Any],
        kwargs: dict[str, Any],
        expected_params: dict[str, Any],
    ) -> None:
        capture = RequestCapture(payload=[sample_changelog_entry])

        with aioresponses() as m:
            m.get(CHANGELOG_URL_RE, callback=capture.callback)

            await tracker_client.issue_get_changelog("TEST-123", **kwargs)

        capture.assert_called_once()
        capture.last_request.assert_params(expected_params)

    async def test_forwards_auth(
        self,
        tracker_client: TrackerClient,
        sample_changelog_entry: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_changelog_entry])

        with aioresponses() as m:
            m.get(CHANGELOG_URL_RE, callback=capture.callback)

            await tracker_client.issue_get_changelog("TEST-123", auth=yandex_auth)

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
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/changelog?perPage=50",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_changelog("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_other_error_propagates(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(f"{CHANGELOG_URL}?perPage=50", status=400)

            with pytest.raises(ClientResponseError) as exc_info:
                await tracker_client.issue_get_changelog("TEST-123")

            assert exc_info.value.status == 400
