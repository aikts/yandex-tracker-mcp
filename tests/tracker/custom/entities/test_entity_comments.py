import re
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.types.issues import CommentsPage, IssueComment
from tests.aioresponses_utils import RequestCapture

ENTITY_TYPES = [
    ("project", "abc123"),
    ("portfolio", "def456"),
    ("goal", "ghi789"),
]


def _comment_data(entity_type: str, entity_id: str) -> dict[str, Any]:
    return {
        "self": f"https://api.tracker.yandex.net/v3/entities/{entity_type}/{entity_id}/comments/1",
        "id": 1,
        "longId": "65a156a29d5d200000000001",
        "text": f"Comment on {entity_type}",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "createdAt": "2024-01-01T00:00:00.000+0000",
    }


class TestEntityGetComments:
    """Entity comments paginate through the dedicated `_relative` endpoint, which
    answers with an object and signals more pages via `hasNext` (unlike the issue
    comment endpoint, which uses `id` + a `Link` header)."""

    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_success(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        comment_data = _comment_data(entity_type, entity_id)
        capture = RequestCapture(
            payload={"comments": [comment_data], "hasNext": False, "hasPrev": False}
        )

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments/_relative(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_get_comments")
            result = await method(entity_id)

            assert isinstance(result, CommentsPage)
            assert result.next_cursor is None
            assert len(result.comments) == 1
            assert isinstance(result.comments[0], IssueComment)
            assert result.comments[0].text == f"Comment on {entity_type}"

        capture.assert_called_once()
        capture.last_request.assert_params({"perPage": 50})
        assert "from" not in (capture.last_request.params or {})

    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_passes_per_page_and_cursor(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        capture = RequestCapture(
            payload={"comments": [], "hasNext": False, "hasPrev": False}
        )

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments/_relative(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_get_comments")
            await method(entity_id, per_page=10, cursor="42")

        capture.assert_called_once()
        capture.last_request.assert_params({"perPage": 10, "from": "42"})

    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_next_cursor_is_last_comment_long_id_when_has_next(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        first = _comment_data(entity_type, entity_id)
        second = {
            **_comment_data(entity_type, entity_id),
            "id": 2,
            "longId": "65a156a29d5d200000000002",
        }

        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments/_relative(\?.*)?$"
                ),
                payload={"comments": [first, second], "hasNext": True},
            )

            method = getattr(tracker_client, f"{entity_type}_get_comments")
            result = await method(entity_id)

        assert result.next_cursor == "65a156a29d5d200000000002"

    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_no_next_cursor_on_empty_last_page(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        """`hasNext` with no comments must not produce a bogus cursor."""
        with aioresponses() as m:
            m.get(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments/_relative(\?.*)?$"
                ),
                payload={"comments": [], "hasNext": True},
            )

            method = getattr(tracker_client, f"{entity_type}_get_comments")
            result = await method(entity_id)

        assert result.comments == []
        assert result.next_cursor is None


class TestEntityAddComment:
    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_success(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        comment_data = _comment_data(entity_type, entity_id)
        capture = RequestCapture(status=201, payload=comment_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_add_comment")
            result = await method(entity_id, text="Hello")

            assert isinstance(result, IssueComment)
            assert result.id == 1

        capture.assert_called_once()
        capture.last_request.assert_json_body({"text": "Hello"})

    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_with_summonees(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        comment_data = _comment_data(entity_type, entity_id)
        capture = RequestCapture(status=201, payload=comment_data)

        with aioresponses() as m:
            m.post(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_add_comment")
            await method(
                entity_id,
                text="Ping",
                summonees=["user123"],
                maillist_summonees=["team@example.com"],
            )

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "text": "Ping",
                "summonees": ["user123"],
                "maillistSummonees": ["team@example.com"],
            }
        )


class TestEntityUpdateComment:
    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_success(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        comment_data = _comment_data(entity_type, entity_id)
        comment_data["text"] = "Updated text"
        capture = RequestCapture(payload=comment_data)

        with aioresponses() as m:
            m.patch(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments/1(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_update_comment")
            result = await method(entity_id, 1, text="Updated text")

            assert isinstance(result, IssueComment)
            assert result.text == "Updated text"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"text": "Updated text"})


class TestEntityDeleteComment:
    @pytest.mark.parametrize("entity_type,entity_id", ENTITY_TYPES)
    async def test_success(
        self, tracker_client: TrackerClient, entity_type: str, entity_id: str
    ) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                re.compile(
                    rf"^https://api\.tracker\.yandex\.net/v3/entities/{entity_type}/"
                    rf"{entity_id}/comments/1(\?.*)?$"
                ),
                callback=capture.callback,
            )

            method = getattr(tracker_client, f"{entity_type}_delete_comment")
            result = await method(entity_id, 1)

            assert result is None

        capture.assert_called_once()
