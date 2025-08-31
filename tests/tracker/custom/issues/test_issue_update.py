from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.inputs import (
    IssueUpdateFollower,
    IssueUpdateParent,
    IssueUpdatePriority,
    IssueUpdateProject,
    IssueUpdateSprint,
    IssueUpdateType,
)
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


@pytest.fixture
def updated_issue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
        "id": "593cd211ef7e8a33********",
        "key": "TEST-123",
        "version": 2,
        "summary": "Updated issue summary",
        "description": "Updated issue description",
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
        "type": {
            "self": "https://api.tracker.yandex.net/v3/issuetypes/2",
            "id": "2",
            "key": "task",
            "display": "Task",
        },
        "priority": {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "key": "normal",
            "display": "Normal",
        },
    }


class TestIssueUpdate:
    async def test_success_update_summary(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                summary="Updated issue summary",
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-123"
            assert result.summary == "Updated issue summary"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"summary": "Updated issue summary"})

    async def test_success_update_description(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                description="Updated issue description",
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {"description": "Updated issue description"}
        )

    async def test_success_update_with_markup_type(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                description="**Bold text**",
                markup_type="markdown",
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["description"] == "**Bold text**"
        assert body["markupType"] == "markdown"

    async def test_success_update_parent(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                parent=IssueUpdateParent(key="TEST-100"),
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["parent"] == {"key": "TEST-100"}

    async def test_success_update_sprint(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                sprint=[
                    IssueUpdateSprint(id=1),
                    IssueUpdateSprint(id=2),
                ],
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["sprint"] == [{"id": 1}, {"id": 2}]

    async def test_success_update_type(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                type=IssueUpdateType(key="bug"),
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["type"] == {"key": "bug"}

    async def test_success_update_priority(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                priority=IssueUpdatePriority(key="critical"),
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["priority"] == {"key": "critical"}

    async def test_success_update_followers(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                followers=[
                    IssueUpdateFollower(id="user1"),
                    IssueUpdateFollower(id="user2"),
                ],
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["followers"] == [{"id": "user1"}, {"id": "user2"}]

    async def test_success_update_project(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                project=IssueUpdateProject(primary=123, secondary=[456, 789]),
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["project"] == {"primary": 123, "secondary": [456, 789]}

    async def test_success_update_tags(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                tags=["urgent", "backend"],
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["tags"] == ["urgent", "backend"]

    async def test_success_update_attachment_ids(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                attachment_ids=["attach-1", "attach-2"],
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["attachmentIds"] == ["attach-1", "attach-2"]

    async def test_success_with_version_param(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123?version=1",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                summary="Updated summary",
                version=1,
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        capture.last_request.assert_params({"version": 1})

    async def test_success_with_kwargs(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                customField="custom value",
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["customField"] == "custom value"

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        updated_issue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issue_update(
                "TEST-123",
                summary="Updated summary",
                auth=yandex_auth_cloud,
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/NOTFOUND-123",
                status=404,
            )

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_update("NOTFOUND-123", summary="New summary")

            assert exc_info.value.issue_id == "NOTFOUND-123"

    async def test_success_update_multiple_fields(
        self, tracker_client: TrackerClient, updated_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=updated_issue_data)

        with aioresponses() as m:
            m.patch(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_update(
                "TEST-123",
                summary="Updated summary",
                description="Updated description",
                priority=IssueUpdatePriority(key="critical"),
                tags=["urgent"],
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["summary"] == "Updated summary"
        assert body["description"] == "Updated description"
        assert body["priority"] == {"key": "critical"}
        assert body["tags"] == ["urgent"]
