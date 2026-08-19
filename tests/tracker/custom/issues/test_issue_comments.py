from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import CommentsPage, IssueComment

COMMENTS_URL = "https://api.tracker.yandex.net/v3/issues/TEST-123/comments"


class TestIssueGetComments:
    async def test_success(
        self, tracker_client: TrackerClient, sample_comment_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(f"{COMMENTS_URL}?perPage=50", payload=[sample_comment_data])

            result = await tracker_client.issue_get_comments("TEST-123")

            assert isinstance(result, CommentsPage)
            assert result.next_cursor is None
            assert len(result.comments) == 1
            assert isinstance(result.comments[0], IssueComment)
            assert result.comments[0].text == "This is a test comment"

    async def test_passes_per_page_and_cursor(
        self, tracker_client: TrackerClient, sample_comment_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(f"{COMMENTS_URL}?perPage=10&id=42", payload=[sample_comment_data])

            result = await tracker_client.issue_get_comments(
                "TEST-123", per_page=10, cursor="42"
            )

        assert len(result.comments) == 1

    async def test_next_cursor_parsed_from_link_header(
        self, tracker_client: TrackerClient, sample_comment_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                f"{COMMENTS_URL}?perPage=50",
                payload=[sample_comment_data],
                headers={"Link": f'<{COMMENTS_URL}?id=100&perPage=50>; rel="next"'},
            )

            result = await tracker_client.issue_get_comments("TEST-123")

        assert result.next_cursor == "100"

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/comments?perPage=50",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_comments("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"
