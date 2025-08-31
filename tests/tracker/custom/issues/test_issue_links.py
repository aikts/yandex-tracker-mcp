import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueLink


class TestIssuesGetLinks:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        link_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/links/1",
            "id": 123,
            "type": {
                "self": "https://api.tracker.yandex.net/v3/linkTypes/relates",
                "id": "relates",
                "inward": "relates to",
                "outward": "relates to",
            },
            "direction": "outward",
            "object": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-124",
                "id": "issue-124",
                "key": "TEST-124",
                "display": "Related issue",
            },
        }
        links_response = [link_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/links",
                payload=links_response,
            )

            result = await tracker_client.issues_get_links("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueLink)

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/links",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issues_get_links("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"
