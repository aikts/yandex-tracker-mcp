from typing import Any

import pytest
from aioresponses import aioresponses
from pydantic import BaseModel, ValidationError

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import TrackerAPIError
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.inputs import (
    IssueComponentRef,
    IssueFollowerRef,
    IssueParentRef,
    IssuePriorityRef,
    IssueProjectRef,
    IssueSprintRef,
    IssueTypeRef,
)
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


@pytest.fixture
def created_issue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-456",
        "id": "593cd211ef7e8a33********",
        "key": "TEST-456",
        "version": 1,
        "summary": "New issue summary",
        "description": "New issue description",
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


class TestIssueCreate:
    async def test_success_minimal(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"
            assert result.summary == "New issue summary"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
            }
        )

    async def test_success_with_description(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                description="New issue description",
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
                "description": "New issue description",
            }
        )

    async def test_success_with_all_params(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                description="New issue description",
                type=2,
                assignee="user123",
                priority="normal",
                parent="TEST-100",
                sprint=["sprint1", "sprint2"],
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
                "description": "New issue description",
                "type": 2,
                "assignee": "user123",
                "priority": "normal",
                "parent": "TEST-100",
                "sprint": ["sprint1", "sprint2"],
            }
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        created_issue_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.issue_create(
                queue="TEST",
                summary="New issue summary",
                auth=yandex_auth_cloud,
            )

            assert isinstance(result, Issue)
            assert result.key == "TEST-456"

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_with_assignee_as_int(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                assignee=1234567890,
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["assignee"] == 1234567890

    async def test_with_priority_as_int(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                priority=2,
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["priority"] == 2

    async def test_reference_fields_are_sent_unambiguously(
        self, tracker_client: TrackerClient, created_issue_data: dict[str, Any]
    ) -> None:
        """Reference fields serialize the same way create and update do.

        Bare strings would be resolved by Tracker as names/logins, which is what
        made a create with `components: ["694"]` / `followers: ["8000...34"]`
        fail with 422 while the very same values worked in an update.
        """
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            result = await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                markup_type="md",
                type=IssueTypeRef(key="task"),
                priority=IssuePriorityRef(key="normal"),
                parent=IssueParentRef(key="TEST-100"),
                sprint=[IssueSprintRef(id=42)],
                followers=[IssueFollowerRef(id="8000000000000034")],
                components=[IssueComponentRef(id=694)],
                tags=["tag1"],
                project=IssueProjectRef(primary=49),
            )

            assert isinstance(result, Issue)

        capture.assert_called_once()
        capture.last_request.assert_json_body(
            {
                "queue": "TEST",
                "summary": "New issue summary",
                "markupType": "md",
                "type": {"key": "task"},
                "priority": {"key": "normal"},
                "parent": {"key": "TEST-100"},
                "sprint": [{"id": 42}],
                "followers": [{"id": "8000000000000034"}],
                "components": [694],
                "tags": ["tag1"],
                "project": {"primary": 49},
            }
        )

    @pytest.mark.parametrize(
        ("component", "expected"),
        [
            (IssueComponentRef(id=694), 694),
            # A numeric string is an ID the caller copied out of a JSON payload,
            # not a component named "694".
            (IssueComponentRef.model_validate({"id": "694"}), 694),
            (IssueComponentRef(name="Backend"), "Backend"),
        ],
    )
    async def test_component_reference_serialization(
        self,
        tracker_client: TrackerClient,
        created_issue_data: dict[str, Any],
        component: IssueComponentRef,
        expected: int | str,
    ) -> None:
        capture = RequestCapture(payload=created_issue_data)

        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                callback=capture.callback,
            )

            await tracker_client.issue_create(
                queue="TEST",
                summary="New issue summary",
                components=[component],
            )

        capture.assert_called_once()
        body = capture.last_request.get_json_body()
        assert body["components"] == [expected]

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"id": 694, "name": "Backend"},
        ],
    )
    def test_component_reference_requires_exactly_one_of_id_or_name(
        self, payload: dict[str, Any]
    ) -> None:
        with pytest.raises(ValidationError):
            IssueComponentRef.model_validate(payload)

    async def test_api_error_carries_tracker_explanation(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.post(
                "https://api.tracker.yandex.net/v3/issues",
                status=422,
                payload={
                    "errors": {"components": "Component not found"},
                    "errorMessages": ["Issue was not created"],
                    "statusCode": 422,
                },
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.issue_create(queue="TEST", summary="Summary")

        assert exc_info.value.status == 422
        assert exc_info.value.errors == {"components": "Component not found"}
        assert "Issue was not created" in str(exc_info.value)
        assert "components: Component not found" in str(exc_info.value)


class TestReferenceModelValidation:
    """An empty reference object gives Tracker nothing to resolve, and its own
    answer to `{"type": {}}` is an unhelpful 400/422 - so it is refused here."""

    @pytest.mark.parametrize(
        "model",
        [IssueParentRef, IssueTypeRef, IssuePriorityRef],
        ids=lambda model: model.__name__,
    )
    def test_empty_reference_is_rejected(self, model: type[BaseModel]) -> None:
        with pytest.raises(ValidationError) as exc_info:
            model()

        assert "requires 'id' or 'key'" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("model", "kwargs"),
        [
            (IssueParentRef, {"key": "QUEUE-1"}),
            (IssueParentRef, {"id": "1"}),
            (IssueTypeRef, {"key": "bug"}),
            (IssuePriorityRef, {"id": "3"}),
            (IssuePriorityRef, {"id": "3", "key": "normal"}),
        ],
        ids=["parent-key", "parent-id", "type-key", "priority-id", "priority-both"],
    )
    def test_a_populated_reference_is_accepted(
        self, model: type[BaseModel], kwargs: dict[str, str]
    ) -> None:
        assert model(**kwargs)
