from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueComment


class TestIssueGetComments:
    async def test_success(
        self, tracker_client: TrackerClient, sample_comment_data: dict[str, Any]
    ) -> None:
        comments_response = [sample_comment_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments",
                payload=comments_response,
            )

            result = await tracker_client.issue_get_comments("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueComment)
            assert result[0].text == "This is a test comment"

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/comments",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get_comments("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"
