import datetime
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.inputs import (
    ChecklistItemDeadlineInput,
    ChecklistItemInput,
)
from mcp_tracker.tracker.proto.types.issues import ChecklistItem
from tests.aioresponses_utils import RequestCapture


@pytest.fixture
def issue_with_checklist() -> dict[str, Any]:
    """Issue payload as returned by the checklist write endpoints."""
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
        "id": "593cd211ef7e8a33********",
        "key": "TEST-123",
        "version": 2,
        "summary": "Test issue summary",
        "checklistItems": [
            {
                "id": "item-1",
                "text": "First item",
                "textHtml": "First item",
                "checked": False,
                "checklistItemType": "standard",
            },
            {
                "id": "item-2",
                "text": "Second item",
                "checked": True,
                "checklistItemType": "standard",
            },
        ],
    }


class TestIssueAddChecklistItems:
    async def test_adds_single_item(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=issue_with_checklist)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                callback=capture.callback,
            )

            result = await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[ChecklistItemInput(text="First item")],
            )

            assert len(result) == 2
            assert isinstance(result[0], ChecklistItem)
            assert result[0].id == "item-1"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"text": "First item"})
        capture.last_request.assert_header("Authorization", "OAuth test-token")
        capture.last_request.assert_header("X-Org-ID", "test-org")

    async def test_adds_item_with_all_fields(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=issue_with_checklist)
        deadline = datetime.datetime(2021, 5, 25, 0, 0, 0, tzinfo=datetime.timezone.utc)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                callback=capture.callback,
            )

            await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[
                    ChecklistItemInput(
                        text="First item",
                        checked=True,
                        assignee="user123",
                        deadline=ChecklistItemDeadlineInput(
                            date=deadline, deadline_type="quarter"
                        ),
                    )
                ],
            )

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "text": "First item",
                "checked": True,
                "assignee": "user123",
                "deadline": {
                    "date": "2021-05-25T00:00:00.000000+0000",
                    "deadlineType": "quarter",
                },
            }
        )

    async def test_naive_deadline_is_treated_as_utc(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=issue_with_checklist)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                callback=capture.callback,
            )

            await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[
                    ChecklistItemInput(
                        text="First item",
                        deadline=ChecklistItemDeadlineInput(
                            date=datetime.datetime(2021, 5, 25, 10, 30)
                        ),
                    )
                ],
            )

        capture.last_request.assert_json_field(
            "deadline",
            {"date": "2021-05-25T10:30:00.000000+0000", "deadlineType": "date"},
        )

    async def test_adds_items_one_request_per_item(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=issue_with_checklist)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                callback=capture.callback,
                repeat=True,
            )

            result = await tracker_client.issue_add_checklist_items(
                "TEST-123",
                items=[
                    ChecklistItemInput(text="First item"),
                    ChecklistItemInput(text="Second item"),
                ],
            )

            assert len(result) == 2

        capture.assert_request_count(2)
        assert capture.requests[0].get_json_body() == {"text": "First item"}
        assert capture.requests[1].get_json_body() == {"text": "Second item"}

    async def test_empty_items_raises_error(
        self, tracker_client: TrackerClient
    ) -> None:
        with pytest.raises(ValueError):
            await tracker_client.issue_add_checklist_items("TEST-123", items=[])

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/checklistItems",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_add_checklist_items(
                    "NOTFOUND-123",
                    items=[ChecklistItemInput(text="First item")],
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueUpdateChecklistItem:
    async def test_updates_item(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=issue_with_checklist)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems/item-1",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update_checklist_item(
                "TEST-123",
                "item-1",
                text="Updated item",
                checked=True,
                assignee="user123",
            )

            assert len(result) == 2
            assert isinstance(result[0], ChecklistItem)

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"text": "Updated item", "checked": True, "assignee": "user123"}
        )

    async def test_reuses_current_text_when_text_is_omitted(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        checklist_capture = RequestCapture(
            payload=issue_with_checklist["checklistItems"]
        )
        patch_capture = RequestCapture(payload=issue_with_checklist)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                callback=checklist_capture.callback,
            )
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems/item-2",
                callback=patch_capture.callback,
            )

            await tracker_client.issue_update_checklist_item(
                "TEST-123",
                "item-2",
                checked=False,
            )

        checklist_capture.assert_called_once()
        patch_capture.assert_called_once()
        patch_capture.last_request.assert_json_body(
            {"text": "Second item", "checked": False}
        )

    async def test_unknown_item_without_text_raises_error(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                payload=issue_with_checklist["checklistItems"],
            )

            with pytest.raises(ValueError):
                await tracker_client.issue_update_checklist_item(
                    "TEST-123",
                    "unknown-item",
                    checked=True,
                )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/checklistItems/item-1",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_update_checklist_item(
                    "NOTFOUND-123",
                    "item-1",
                    text="Updated item",
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueDeleteChecklistItem:
    async def test_deletes_item(
        self, tracker_client: TrackerClient, issue_with_checklist: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=issue_with_checklist)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems/item-1",
                callback=capture.callback,
            )

            result = await tracker_client.issue_delete_checklist_item(
                "TEST-123", "item-1"
            )

            assert len(result) == 2
            assert isinstance(result[0], ChecklistItem)

        capture.assert_called_once()
        capture.last_request.assert_header("Authorization", "OAuth test-token")

    async def test_returns_empty_checklist_when_response_has_no_items(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems/item-1",
                payload=sample_issue_data,
            )

            result = await tracker_client.issue_delete_checklist_item(
                "TEST-123", "item-1"
            )

            assert result == []

    async def test_returns_empty_checklist_on_empty_body(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems/item-1",
                status=204,
                body="",
            )

            result = await tracker_client.issue_delete_checklist_item(
                "TEST-123", "item-1"
            )

            assert result == []

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/checklistItems/item-1",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_delete_checklist_item(
                    "NOTFOUND-123", "item-1"
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"
