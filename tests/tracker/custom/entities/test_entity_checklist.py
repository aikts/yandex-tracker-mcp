import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import TrackerAPIError
from mcp_tracker.tracker.proto.types.entities import PortfolioEntity, ProjectEntity
from mcp_tracker.tracker.proto.types.inputs import EntityChecklistItemUpdateInput
from tests.aioresponses_utils import RequestCapture

ENTITY_TYPES = [
    ("project", "abc123", ProjectEntity),
    ("portfolio", "def456", PortfolioEntity),
]


def _entity_data(entity_type: str, entity_id: str) -> dict[str, Any]:
    return {
        "self": f"https://api.tracker.yandex.net/v3/entities/{entity_type}/{entity_id}",
        "id": entity_id,
        "shortId": 1,
        "version": 2,
        "entityType": entity_type,
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "fields": {
            "summary": f"Test {entity_type}",
            "checklistItems": [
                {"id": "item1", "text": "Do the thing", "checked": False},
            ],
        },
    }


class TestEntityAddChecklistItem:
    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        capture = RequestCapture(payload=_entity_data(entity_type, entity_id))

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_add_checklist_item")
            result = await method(entity_id, text="Do the thing")

            assert isinstance(result, model)
            assert result.fields is not None
            assert result.fields.checklistItems is not None
            assert result.fields.checklistItems[0].id == "item1"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"text": "Do the thing"})

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_with_all_fields(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        capture = RequestCapture(payload=_entity_data(entity_type, entity_id))
        deadline = {"date": "2026-08-20T00:00:00.000+0000", "deadlineType": "date"}

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_add_checklist_item")
            await method(
                entity_id,
                text="Do the thing",
                checked=True,
                assignee="user123",
                deadline=deadline,
            )

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "text": "Do the thing",
                "checked": True,
                "assignee": "user123",
                "deadline": deadline,
            }
        )


class TestEntityUpdateChecklistItem:
    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        capture = RequestCapture(payload=_entity_data(entity_type, entity_id))

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems/item1(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_update_checklist_item")
            result = await method(entity_id, "item1", checked=True)

            assert isinstance(result, model)

        capture.assert_called_once()
        capture.last_request.assert_json_body({"checked": True})


class TestEntityMoveChecklistItem:
    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        capture = RequestCapture(payload=_entity_data(entity_type, entity_id))

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems/item1/_move(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_move_checklist_item")
            result = await method(entity_id, "item1", before="item0")

            assert isinstance(result, model)

        capture.assert_called_once()
        capture.last_request.assert_json_body({"before": "item0"})


class TestEntityDeleteChecklistItem:
    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        entity_data = _entity_data(entity_type, entity_id)
        entity_data["fields"]["checklistItems"] = []
        capture = RequestCapture(payload=entity_data)

        with aioresponses() as m:
            m.delete(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems/item1(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_delete_checklist_item")
            result = await method(entity_id, "item1")

            assert isinstance(result, model)
            assert result.fields is not None
            assert result.fields.checklistItems == []

        capture.assert_called_once()


class TestEntityUpdateChecklist:
    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        capture = RequestCapture(payload=_entity_data(entity_type, entity_id))
        items = [
            EntityChecklistItemUpdateInput(id="item1", text="Do the thing"),
            EntityChecklistItemUpdateInput(
                id="item2", text="Do another thing", checked=True
            ),
        ]

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_update_checklist")
            result = await method(entity_id, items=items)

            assert isinstance(result, model)

        capture.assert_called_once()
        assert capture.last_request.get_json_body() == [
            {"id": "item1", "text": "Do the thing"},
            {"id": "item2", "text": "Do another thing", "checked": True},
        ]

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_partial_item_list_surfaces_tracker_error(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        """Tracker rejects a payload that omits existing items with a bare 500

        (the bulk endpoint edits the existing set in place rather than
        replacing it, so the item count cannot change). The body carries no
        `errorMessages`/`errors`, so the raw text must still reach the caller
        instead of being swallowed by a bare `raise_for_status()`.
        """
        error_body = "Internal Server Error"

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                status=500,
                body=error_body,
            )

            method = getattr(tracker_client, f"{entity_type}_update_checklist")
            with pytest.raises(TrackerAPIError) as exc_info:
                await method(
                    entity_id,
                    items=[EntityChecklistItemUpdateInput(id="item1", text="Only one")],
                )

        assert exc_info.value.status == 500
        assert error_body in str(exc_info.value)


class TestEntityDeleteChecklist:
    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_success(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        entity_data = _entity_data(entity_type, entity_id)
        entity_data["fields"]["checklistItems"] = []
        capture = RequestCapture(payload=entity_data)

        with aioresponses() as m:
            m.delete(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_delete_checklist")
            result = await method(entity_id)

            assert isinstance(result, model)
            assert result.fields is not None
            assert result.fields.checklistItems == []

        capture.assert_called_once()
