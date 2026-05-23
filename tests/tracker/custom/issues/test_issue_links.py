import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.issues import IssueLink
from tests.aioresponses_utils import RequestCapture


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


class TestIssueAddLink:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        link_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/links/1",
            "id": 1,
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

        capture = RequestCapture(payload=link_data, status=201)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/links",
                callback=capture.callback,
            )

            result = await tracker_client.issue_add_link(
                "TEST-123", relationship="relates", issue="TEST-124"
            )

            assert isinstance(result, IssueLink)
            assert result.id == 1

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"relationship": "relates", "issue": "TEST-124"}
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/links",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_add_link(
                    "NOTFOUND-123", relationship="relates", issue="TEST-124"
                )

            assert exc_info.value.issue_id == "NOTFOUND-123"


class TestIssueDeleteLink:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        capture = RequestCapture(status=204)

        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/links/10",
                callback=capture.callback,
            )

            await tracker_client.issue_delete_link("TEST-123", 10)

        capture.assert_called_once()

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.delete(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/links/10",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_delete_link("NOTFOUND-123", 10)

            assert exc_info.value.issue_id == "NOTFOUND-123"
