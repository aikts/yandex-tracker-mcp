import datetime
import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    ChecklistBatchPartiallyAdded,
    ChecklistItemNotFound,
    IssueNotFound,
    TrackerAPIError,
)
from mcp_tracker.tracker.proto.types.inputs import (
    ChecklistItemDeadlineInput,
    ChecklistItemInput,
)
from tests.aioresponses_utils import RequestCapture

CHECKLIST_ITEMS_URL = re.compile(
    r"^https://api\.tracker\.yandex\.net/v3/issues/TEST-123/checklistItems$"
)
CHECKLIST_ITEM_URL = re.compile(
    r"^https://api\.tracker\.yandex\.net/v3/issues/TEST-123/checklistItems/item-1$"
)


def _issue_data(items: list[dict[str, Any]]) -> dict[str, Any]:
    """The issue payload Tracker answers a checklist mutation with."""
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
        "id": "issue123",
        "key": "TEST-123",
        "summary": "Test issue",
        "checklistItems": items,
    }


class TestIssueAddChecklistItems:
    async def test_adds_single_item(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(
            payload=_issue_data([{"id": "item-1", "text": "Do the thing"}])
        )

        with aioresponses() as m:
            m.post(CHECKLIST_ITEMS_URL, callback=capture.callback)

            result = await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[ChecklistItemInput(text="Do the thing")],
            )

        assert [item.text for item in result] == ["Do the thing"]
        capture.assert_request_count(1)
        capture.last_request.assert_json_body({"text": "Do the thing"})

    async def test_adds_items_sequentially(self, tracker_client: TrackerClient) -> None:
        """Tracker takes one item per request, so a batch turns into N POSTs."""
        capture = RequestCapture(
            payload=_issue_data(
                [
                    {"id": "item-1", "text": "First"},
                    {"id": "item-2", "text": "Second"},
                ]
            )
        )

        with aioresponses() as m:
            m.post(CHECKLIST_ITEMS_URL, callback=capture.callback, repeat=True)

            result = await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[
                    ChecklistItemInput(text="First"),
                    ChecklistItemInput(text="Second"),
                ],
            )

        capture.assert_request_count(2)
        assert [r.get_json_body()["text"] for r in capture.requests] == [
            "First",
            "Second",
        ]
        assert [item.id for item in result] == ["item-1", "item-2"]

    async def test_sends_optional_fields(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(payload=_issue_data([{"id": "item-1", "text": "Do"}]))

        with aioresponses() as m:
            m.post(CHECKLIST_ITEMS_URL, callback=capture.callback)

            await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[
                    ChecklistItemInput(
                        text="Do",
                        checked=True,
                        assignee="i.ivanov",
                        deadline=ChecklistItemDeadlineInput(
                            date=datetime.datetime(
                                2026, 8, 20, tzinfo=datetime.timezone.utc
                            )
                        ),
                    )
                ],
            )

        capture.last_request.assert_json_body(
            {
                "text": "Do",
                "checked": True,
                "assignee": "i.ivanov",
                "deadline": {
                    "date": "2026-08-20T00:00:00.000000+0000",
                    "deadlineType": "date",
                },
            }
        )

    async def test_empty_items_makes_no_request(
        self, tracker_client: TrackerClient
    ) -> None:
        # No mock registered: any request would fail the test.
        with aioresponses():
            assert (
                await tracker_client.issue_add_checklist_items("TEST-123", items=[])
                == []
            )

    async def test_partial_failure_reports_what_landed(
        self, tracker_client: TrackerClient
    ) -> None:
        """A batch is N requests, so a failure partway through is not a no-op."""
        with aioresponses() as m:
            m.post(
                CHECKLIST_ITEMS_URL,
                payload=_issue_data([{"id": "item-1", "text": "First"}]),
            )
            m.post(
                CHECKLIST_ITEMS_URL,
                status=422,
                payload={"errorMessages": ["Checklist item text is empty"]},
            )

            with pytest.raises(ChecklistBatchPartiallyAdded) as exc_info:
                await tracker_client.issue_add_checklist_items(
                    "TEST-123",
                    items=[
                        ChecklistItemInput(text="First"),
                        ChecklistItemInput(text="Second"),
                        ChecklistItemInput(text="Third"),
                    ],
                )

        assert exc_info.value.added == 1
        assert exc_info.value.total == 3
        assert "Checklist item text is empty" in str(exc_info.value)

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-1/checklistItems",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_add_checklist_items(
                    "NOTFOUND-1", items=[ChecklistItemInput(text="Do")]
                )

        assert exc_info.value.issue_id == "NOTFOUND-1"

    async def test_error_body_is_surfaced(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                CHECKLIST_ITEMS_URL,
                status=422,
                payload={"errorMessages": ["Checklist item text is empty"]},
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.issue_add_checklist_items(
                    "TEST-123", items=[ChecklistItemInput(text="Do")]
                )

        assert "Checklist item text is empty" in str(exc_info.value)


class TestIssueUpdateChecklistItem:
    async def test_updates_item(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(
            payload=_issue_data([{"id": "item-1", "text": "New text", "checked": True}])
        )

        with aioresponses() as m:
            m.patch(CHECKLIST_ITEM_URL, callback=capture.callback)

            result = await tracker_client.issue_update_checklist_item(
                "TEST-123", "item-1", text="New text", checked=True
            )

        capture.assert_request_count(1)
        capture.last_request.assert_json_body({"text": "New text", "checked": True})
        assert result[0].checked is True

    async def test_reads_current_text_when_omitted(
        self, tracker_client: TrackerClient
    ) -> None:
        """`text` is required by the API, so it is refilled from the checklist."""
        patch_capture = RequestCapture(
            payload=_issue_data(
                [{"id": "item-1", "text": "Do the thing", "checked": True}]
            )
        )

        with aioresponses() as m:
            m.get(
                CHECKLIST_ITEMS_URL,
                payload=[{"id": "item-1", "text": "Do the thing", "checked": False}],
            )
            m.patch(CHECKLIST_ITEM_URL, callback=patch_capture.callback)

            result = await tracker_client.issue_update_checklist_item(
                "TEST-123", "item-1", checked=True
            )

        patch_capture.last_request.assert_json_body(
            {"text": "Do the thing", "checked": True}
        )
        assert result[0].checked is True

    async def test_unknown_item_id_raises(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            # No PATCH mock: the client must not reach the API with an unknown id.
            m.get(CHECKLIST_ITEMS_URL, payload=[{"id": "item-1", "text": "Do"}])

            with pytest.raises(ChecklistItemNotFound) as exc_info:
                await tracker_client.issue_update_checklist_item(
                    "TEST-123", "missing", checked=True
                )

        assert exc_info.value.checklist_item_id == "missing"

    async def test_unknown_item_id_raises_the_same_error_with_text(
        self, tracker_client: TrackerClient
    ) -> None:
        """Passing `text` must not change which error an unknown item id gives:
        without it the id is checked against the checklist, with it Tracker
        answers 404, and both have to arrive as ChecklistItemNotFound."""
        with aioresponses() as m:
            m.patch(
                re.compile(
                    r"^https://api\.tracker\.yandex\.net/v3/issues/TEST-123/"
                    r"checklistItems/missing$"
                ),
                status=404,
            )

            with pytest.raises(ChecklistItemNotFound) as exc_info:
                await tracker_client.issue_update_checklist_item(
                    "TEST-123", "missing", text="New text"
                )

        assert exc_info.value.checklist_item_id == "missing"

    async def test_not_found_names_both_causes(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.delete(CHECKLIST_ITEM_URL, status=404)

            with pytest.raises(ChecklistItemNotFound) as exc_info:
                await tracker_client.issue_delete_checklist_item("TEST-123", "item-1")

        assert exc_info.value.checklist_item_id == "item-1"
        with aioresponses() as m:
            m.patch(CHECKLIST_ITEM_URL, status=404)

            with pytest.raises(ChecklistItemNotFound) as exc_info:
                await tracker_client.issue_update_checklist_item(
                    "TEST-123", "item-1", text="New text"
                )

        assert exc_info.value.checklist_item_id == "item-1"
        assert exc_info.value.entity_id == "TEST-123"
        assert "does not exist" in str(exc_info.value)


class TestIssueDeleteChecklistItem:
    async def test_deletes_item(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(
            payload=_issue_data([{"id": "item-2", "text": "Second"}])
        )

        with aioresponses() as m:
            m.delete(CHECKLIST_ITEM_URL, callback=capture.callback)

            result = await tracker_client.issue_delete_checklist_item(
                "TEST-123", "item-1"
            )

        capture.assert_request_count(1)
        assert [item.id for item in result] == ["item-2"]

    async def test_last_item_leaves_empty_checklist(
        self, tracker_client: TrackerClient
    ) -> None:
        """Tracker drops the `checklistItems` key once the checklist is empty."""
        with aioresponses() as m:
            m.delete(
                CHECKLIST_ITEM_URL,
                payload={"key": "TEST-123", "summary": "Test issue"},
            )

            assert (
                await tracker_client.issue_delete_checklist_item("TEST-123", "item-1")
                == []
            )

    async def test_not_found_names_both_causes(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.delete(CHECKLIST_ITEM_URL, status=404)

            with pytest.raises(ChecklistItemNotFound) as exc_info:
                await tracker_client.issue_delete_checklist_item("TEST-123", "item-1")

        assert exc_info.value.checklist_item_id == "item-1"
