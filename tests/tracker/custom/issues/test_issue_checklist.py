import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import ChecklistItem


class TestIssueGetChecklist:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        checklist_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems/1",
            "id": "checklist-123",
            "text": "Complete task A",
            "checked": False,
            "checklistItemType": "standard",
        }
        checklist_response = [checklist_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/checklistItems",
                payload=checklist_response,
            )

            result = await tracker_client.issue_get_checklist("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], ChecklistItem)
            assert result[0].text == "Complete task A"

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/checklistItems",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_checklist("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"
