import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import ChecklistItemNotFound, TrackerAPIError
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


def _checklist_snapshot_data(
    entity_type: str, entity_id: str, items: list[dict[str, Any]]
) -> dict[str, Any]:
    data = _entity_data(entity_type, entity_id)
    data["fields"] = {"checklistItems": items}
    return data


class TestEntityUpdateChecklist:
    """`*_update_checklist` reconciles a caller's partial edit against the
    entity's current checklist (fetched via GET) before sending Tracker's bulk
    endpoint the full item array it requires - see
    `TrackerClient._reconcile_checklist_update`. Every test here therefore
    mocks both the GET and the PATCH.
    """

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_untouched_items_are_resent_verbatim(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        current_items = [
            {"id": "item1", "text": "Old text", "checked": False},
            {
                "id": "item2",
                "text": "Do another thing",
                "checked": True,
                "assignee": {"id": "user456", "display": "Someone"},
                "deadline": {
                    "date": "2026-08-20T00:00:00.000+0000",
                    "deadlineType": "date",
                    "isExceeded": False,
                },
            },
        ]
        get_capture = RequestCapture(
            payload=_checklist_snapshot_data(entity_type, entity_id, current_items)
        )
        patch_capture = RequestCapture(payload=_entity_data(entity_type, entity_id))

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}\?fields=checklistItems$"
                ),
                callback=get_capture.callback,
            )
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=patch_capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_update_checklist")
            result = await method(
                entity_id,
                items=[EntityChecklistItemUpdateInput(id="item1", text="Do the thing")],
            )

            assert isinstance(result, model)

        get_capture.assert_called_once()
        patch_capture.assert_called_once()
        body = patch_capture.last_request.get_json_body()
        assert isinstance(body, list)
        assert body[0] == {"id": "item1", "text": "Do the thing", "checked": False}
        # item2 was not mentioned by the caller, so it is resent as-is - including
        # its assignee (converted from a UserReference back to a bare id) and
        # deadline (converted from ChecklistItemDeadline back to a request body).
        assert body[1]["id"] == "item2"
        assert body[1]["text"] == "Do another thing"
        assert body[1]["checked"] is True
        assert body[1]["assignee"] == "user456"
        assert body[1]["deadline"]["deadlineType"] == "date"

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_untouched_item_with_numeric_assignee_id_is_resent(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        """Tracker returns a real user's assignee `id` as a number (verified

        against the live API), not the string this server's request models
        expect - resending it verbatim used to fail local pydantic validation
        for `EntityChecklistItemUpdateInput.assignee: str | None` before the
        current item is converted to `str(...)`.
        """
        current_items = [
            {"id": "item1", "text": "Do the thing", "checked": False},
            {
                "id": "item2",
                "text": "Assigned to someone",
                "checked": False,
                "assignee": {"id": 8000000000000036, "display": "Someone"},
            },
        ]
        get_capture = RequestCapture(
            payload=_checklist_snapshot_data(entity_type, entity_id, current_items)
        )
        patch_capture = RequestCapture(payload=_entity_data(entity_type, entity_id))

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}\?fields=checklistItems$"
                ),
                callback=get_capture.callback,
            )
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=patch_capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_update_checklist")
            await method(
                entity_id,
                items=[EntityChecklistItemUpdateInput(id="item1", text="Do the thing")],
            )

        body = patch_capture.last_request.get_json_body()
        assert isinstance(body, list)
        assert body[1]["assignee"] == "8000000000000036"

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_override_only_changes_fields_the_caller_set(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        current_items = [
            {
                "id": "item1",
                "text": "Old text",
                "checked": True,
                "assignee": {"id": "user456"},
            },
        ]
        get_capture = RequestCapture(
            payload=_checklist_snapshot_data(entity_type, entity_id, current_items)
        )
        patch_capture = RequestCapture(payload=_entity_data(entity_type, entity_id))

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}\?fields=checklistItems$"
                ),
                callback=get_capture.callback,
            )
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/checklistItems(\?.*)?$"
                ),
                callback=patch_capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_update_checklist")
            # Only `text` changes; `checked`/`assignee` are left unset by the
            # caller and must be carried over from the current item, not reset.
            await method(
                entity_id,
                items=[EntityChecklistItemUpdateInput(id="item1", text="New text")],
            )

        body = patch_capture.last_request.get_json_body()
        assert body == [
            {
                "id": "item1",
                "text": "New text",
                "checked": True,
                "assignee": "user456",
            }
        ]

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_unknown_item_id_raises_without_calling_patch(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        current_items = [{"id": "item1", "text": "Do the thing", "checked": False}]
        get_capture = RequestCapture(
            payload=_checklist_snapshot_data(entity_type, entity_id, current_items)
        )

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}\?fields=checklistItems$"
                ),
                callback=get_capture.callback,
            )
            # No PATCH mock registered: if the client called it despite the
            # unknown id, aioresponses would raise a connection error and fail
            # the test.

            method = getattr(tracker_client, f"{entity_type}_update_checklist")
            with pytest.raises(ChecklistItemNotFound) as exc_info:
                await method(
                    entity_id,
                    items=[EntityChecklistItemUpdateInput(id="missing", text="Nope")],
                )

        assert exc_info.value.checklist_item_id == "missing"
        get_capture.assert_called_once()

    @pytest.mark.parametrize("entity_type,entity_id,model", ENTITY_TYPES)
    async def test_tracker_error_on_patch_surfaces_body(
        self,
        tracker_client: TrackerClient,
        entity_type: str,
        entity_id: str,
        model: type[ProjectEntity] | type[PortfolioEntity],
    ) -> None:
        """Even with a reconciled, full item list, Tracker can still reject the
        PATCH (e.g. a 423 version-lock) - its error body must still reach the
        caller instead of being swallowed by a bare `raise_for_status()`.
        """
        current_items = [{"id": "item1", "text": "Do the thing", "checked": False}]
        get_capture = RequestCapture(
            payload=_checklist_snapshot_data(entity_type, entity_id, current_items)
        )
        error_body = "Internal Server Error"

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}\?fields=checklistItems$"
                ),
                callback=get_capture.callback,
            )
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
