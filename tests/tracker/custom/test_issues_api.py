import json
from typing import Any, AsyncGenerator

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)


class TestIssuesAPI:
    @pytest.fixture
    async def client(self) -> AsyncGenerator[TrackerClient, None]:
        client = TrackerClient(
            token="test-token",
            org_id="test-org",
            base_url="https://api.tracker.yandex.net",
        )
        yield client
        await client.close()

    @pytest.fixture
    async def client_no_org(self) -> AsyncGenerator[TrackerClient, None]:
        client = TrackerClient(
            token="test-token",
            base_url="https://api.tracker.yandex.net",
        )
        yield client
        await client.close()

    @pytest.fixture
    def sample_issue_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
            "id": "593cd211ef7e8a33********",
            "key": "TEST-123",
            "version": 1,
            "summary": "Test issue summary",
            "description": "Test issue description",
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "key": "open",
                "display": "Open",
            },
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
        }

    @pytest.fixture
    def sample_comment_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/1",
            "id": 123,
            "text": "This is a test comment",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
        }

    async def test_issue_get_success(
        self, client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                payload=sample_issue_data,
            )

            result = await client.issue_get("TEST-123")

            assert isinstance(result, Issue)
            assert result.key == "TEST-123"
            assert result.summary == "Test issue summary"
            assert result.description == "Test issue description"

    async def test_issue_get_with_auth(
        self, client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        auth = YandexAuth(token="auth-token", org_id="auth-org")

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                payload=sample_issue_data,
            )

            result = await client.issue_get("TEST-123", auth=auth)

            assert isinstance(result, Issue)
            assert result.key == "TEST-123"

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Org-ID"] == "auth-org"

    async def test_issue_get_not_found(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/issues/NOTFOUND-123", status=404)

            with pytest.raises(IssueNotFound) as exc_info:
                await client.issue_get("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_issues_find_success(
        self, client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        search_response = [sample_issue_data]

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=1&perPage=15",
                payload=search_response,
            )

            result = await client.issues_find("Queue: TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Issue)
            assert result[0].key == "TEST-123"

    async def test_issues_find_with_pagination(
        self, client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        search_response = [sample_issue_data]

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues/_search?page=2&perPage=50",
                payload=search_response,
            )

            result = await client.issues_find("Queue: TEST", per_page=50, page=2)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify request parameters
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["params"]["perPage"] == 50
            assert request.kwargs["params"]["page"] == 2

            # Verify request body
            if request.kwargs.get("data"):
                body = json.loads(request.kwargs["data"])
                assert body["query"] == "Queue: TEST"

    async def test_issue_get_comments_success(
        self, client: TrackerClient, sample_comment_data: dict[str, Any]
    ) -> None:
        comments_response = [sample_comment_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/comments",
                payload=comments_response,
            )

            result = await client.issue_get_comments("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueComment)
            assert result[0].text == "This is a test comment"

    async def test_issue_get_comments_not_found(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/comments",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await client.issue_get_comments("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_issues_get_links_success(self, client: TrackerClient) -> None:
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

            result = await client.issues_get_links("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueLink)

    async def test_issues_get_links_not_found(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/links",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await client.issues_get_links("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_issue_get_worklogs_success(self, client: TrackerClient) -> None:
        worklog_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog/1",
            "id": 123,
            "version": 1,
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
                "id": "issue-123",
                "key": "TEST-123",
                "display": "Test issue",
            },
            "comment": "Work done on the issue",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
            "duration": "PT4H",
        }
        worklogs_response = [worklog_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/worklog",
                payload=worklogs_response,
            )

            result = await client.issue_get_worklogs("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Worklog)
            assert result[0].comment == "Work done on the issue"

    async def test_issue_get_worklogs_not_found(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/worklog",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await client.issue_get_worklogs("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_issue_get_attachments_success(self, client: TrackerClient) -> None:
        attachment_data = {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/1",
            "id": "attachment-123",
            "name": "test_file.txt",
            "content": "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/1/content",
            "createdBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Test User",
            },
            "createdAt": "2023-01-01T12:00:00.000+0000",
            "mimetype": "text/plain",
            "size": 1024,
        }
        attachments_response = [attachment_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments",
                payload=attachments_response,
            )

            result = await client.issue_get_attachments("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueAttachment)
            assert result[0].name == "test_file.txt"

    async def test_issue_get_attachments_not_found(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/attachments",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await client.issue_get_attachments("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_issue_get_checklist_success(self, client: TrackerClient) -> None:
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

            result = await client.issue_get_checklist("TEST-123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], ChecklistItem)
            assert result[0].text == "Complete task A"

    async def test_issue_get_checklist_not_found(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123/checklistItems",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await client.issue_get_checklist("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_issues_count_success(self, client: TrackerClient) -> None:
        with aioresponses() as m:
            m.post("https://api.tracker.yandex.net/v3/issues/_count", body="42")

            result = await client.issues_count("Queue: TEST")

            assert result == 42

            # Verify request body
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            if request.kwargs.get("data"):
                body = json.loads(request.kwargs["data"])
                assert body["query"] == "Queue: TEST"

    async def test_issues_count_with_auth(self, client_no_org: TrackerClient) -> None:
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")

        with aioresponses() as m:
            m.post("https://api.tracker.yandex.net/v3/issues/_count", body="10")

            result = await client_no_org.issues_count("Status: Open", auth=auth)

            assert result == 10

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"
