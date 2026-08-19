from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    IssueTemplateNotFound,
    QueueNotFound,
)
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.templates import IssueTemplate
from tests.aioresponses_utils import RequestCapture


class TestIssueTemplates:
    @pytest.fixture
    def sample_template_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/issueTemplates/1",
            "id": "1",
            "version": 2,
            "name": "Bug report",
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "1",
                "key": "TEST",
                "display": "Test Queue",
            },
            "fieldTemplates": {
                "summary": "Bug: ",
                "description": "## Steps to reproduce\n\n## Expected\n\n## Actual",
                "type": {"id": "1", "key": "bug"},
            },
        }

    async def test_get_issue_templates_success(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates?page=1&perPage=50",
                payload=[sample_template_data],
            )

            result = (await tracker_client.get_issue_templates()).values

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueTemplate)
            assert result[0].id == "1"
            assert result[0].name == "Bug report"
            assert result[0].queue is not None
            assert result[0].queue.key == "TEST"
            assert result[0].fieldTemplates is not None
            assert result[0].fieldTemplates["summary"] == "Bug: "

    async def test_get_issue_templates_empty(
        self, tracker_client: TrackerClient
    ) -> None:
        templates_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates?page=1&perPage=50",
                payload=templates_response,
            )

            result = (await tracker_client.get_issue_templates()).values

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_get_issue_templates_with_auth(
        self,
        tracker_client: TrackerClient,
        sample_template_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_template_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates?page=1&perPage=50",
                callback=capture.callback,
            )

            result = (await tracker_client.get_issue_templates(auth=yandex_auth)).values

            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_get_issue_templates_pagination_params(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        """The endpoint paginates with a default of 50 items per page, so both
        values have to reach the API for a caller to see everything."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates?page=3&perPage=25",
                payload=[sample_template_data],
            )

            result = (
                await tracker_client.get_issue_templates(per_page=25, page=3)
            ).values

            assert len(result) == 1

    async def test_get_issue_templates_of_queue(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        """A queue switches the request to the queue-scoped endpoint, which
        returns that queue's templates plus the ones bound to no queue."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/issueTemplates?page=1&perPage=50",
                payload=[sample_template_data],
            )

            result = (await tracker_client.get_issue_templates(queue="TEST")).values

            assert len(result) == 1
            assert result[0].id == "1"

    async def test_get_issue_templates_of_missing_queue(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/NOPE/issueTemplates?page=1&perPage=50",
                status=404,
            )

            with pytest.raises(QueueNotFound) as exc_info:
                await tracker_client.get_issue_templates(queue="NOPE")

            assert exc_info.value.queue_id == "NOPE"

    async def test_get_issue_template_success(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates/1",
                payload=sample_template_data,
            )

            result = await tracker_client.get_issue_template("1")

            assert isinstance(result, IssueTemplate)
            assert result.id == "1"
            assert result.version == 2
            assert result.name == "Bug report"

    async def test_get_issue_template_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_template_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_template_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates/1",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.get_issue_template(
                "1", auth=yandex_auth_cloud
            )

            assert result.id == "1"

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_get_issue_template_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates/missing",
                status=404,
            )

            with pytest.raises(IssueTemplateNotFound) as exc_info:
                await tracker_client.get_issue_template("missing")

            assert exc_info.value.template_id == "missing"

    async def test_undocumented_fields_are_preserved(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        """The endpoint is not in the public API reference, so unknown keys must
        reach the caller rather than being dropped by the model."""
        payload = {**sample_template_data, "someUndocumentedField": {"nested": 1}}

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/issueTemplates/1", payload=payload)

            result = await tracker_client.get_issue_template("1")

            dumped = result.model_dump(by_alias=True)
            assert dumped["someUndocumentedField"] == {"nested": 1}
            assert dumped["self"] == payload["self"]

    @pytest.mark.parametrize("template_id", ["1", 42])
    async def test_id_accepts_string_and_integer(
        self, tracker_client: TrackerClient, template_id: str | int
    ) -> None:
        """Tracker uses both integer and string ids across entities and the
        official client declares no type for template ids."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issueTemplates?page=1&perPage=50",
                payload=[{"id": template_id, "name": "Template"}],
            )

            result = (await tracker_client.get_issue_templates()).values

            assert result[0].id == template_id


class TestTemplateDescription:
    """Tracker sends "" for some templates and omits the key for others; both
    mean the same thing, and neither is the issue body."""

    @pytest.mark.parametrize(
        "payload",
        [{"id": "1", "name": "T", "description": ""}, {"id": "1", "name": "T"}],
        ids=["empty-string", "key-absent"],
    )
    async def test_no_description_reads_the_same_either_way(
        self, tracker_client: TrackerClient, payload: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/issueTemplates/1", payload=payload)

            template = await tracker_client.get_issue_template("1")

            assert template.description is None
            assert "description" not in template.model_dump(by_alias=True)

    async def test_the_issue_body_stays_in_field_templates(
        self, tracker_client: TrackerClient
    ) -> None:
        payload = {
            "id": "1",
            "name": "Bug report",
            "description": "when to use this template",
            "fieldTemplates": {"description": "## Steps to reproduce"},
        }

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/issueTemplates/1", payload=payload)

            template = await tracker_client.get_issue_template("1")

            assert template.description == "when to use this template"
            assert template.fieldTemplates is not None
            assert template.fieldTemplates["description"] == "## Steps to reproduce"
