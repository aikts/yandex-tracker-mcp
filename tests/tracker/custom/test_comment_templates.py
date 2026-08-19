from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    CommentTemplateNotFound,
    QueueNotFound,
)
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.templates import CommentTemplate
from tests.aioresponses_utils import RequestCapture


class TestCommentTemplates:
    @pytest.fixture
    def sample_template_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/commentTemplates/1",
            "id": "1",
            "version": 2,
            "name": "Incident acknowledged",
            "description": "First reply on an incident",
            "template": "Мы получили заявку и начали разбор.",
            "summonees": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1",
                    "id": "1",
                    "display": "Ivan Ivanov",
                    "cloudUid": "cloud-1",
                    "passportUid": 12345,
                }
            ],
            "maillistSummonees": [
                {"id": "duty@example.com", "display": "Duty"},
            ],
            "queue": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST",
                "id": "1",
                "key": "TEST",
                "display": "Test Queue",
            },
        }

    async def test_get_comment_templates_success(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates?page=1&perPage=50",
                payload=[sample_template_data],
            )

            result = (await tracker_client.get_comment_templates()).values

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], CommentTemplate)
            assert result[0].id == "1"
            assert result[0].name == "Incident acknowledged"
            assert result[0].template == "Мы получили заявку и начали разбор."
            assert result[0].description == "First reply on an incident"
            assert result[0].queue is not None
            assert result[0].queue.key == "TEST"

    async def test_summonees_are_parsed(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates?page=1&perPage=50",
                payload=[sample_template_data],
            )

            result = (await tracker_client.get_comment_templates()).values

            template = result[0]
            assert template.summonees is not None
            assert len(template.summonees) == 1
            assert template.summonees[0].display == "Ivan Ivanov"
            assert template.summonees[0].cloud_uid == "cloud-1"
            assert template.maillistSummonees is not None
            assert len(template.maillistSummonees) == 1
            assert template.maillistSummonees[0].id == "duty@example.com"

    async def test_get_comment_templates_empty(
        self, tracker_client: TrackerClient
    ) -> None:
        templates_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates?page=1&perPage=50",
                payload=templates_response,
            )

            result = (await tracker_client.get_comment_templates()).values

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_get_comment_templates_with_auth(
        self,
        tracker_client: TrackerClient,
        sample_template_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_template_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates?page=1&perPage=50",
                callback=capture.callback,
            )

            result = (
                await tracker_client.get_comment_templates(auth=yandex_auth)
            ).values

            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_get_comment_templates_pagination_params(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        """The endpoint paginates with a default of 50 items per page, so both
        values have to reach the API for a caller to see everything."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates?page=3&perPage=25",
                payload=[sample_template_data],
            )

            result = (
                await tracker_client.get_comment_templates(per_page=25, page=3)
            ).values

            assert len(result) == 1

    async def test_get_comment_templates_of_queue(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        """A queue switches the request to the queue-scoped endpoint, which
        returns that queue's templates plus the ones bound to no queue."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/commentTemplates?page=1&perPage=50",
                payload=[sample_template_data],
            )

            result = (await tracker_client.get_comment_templates(queue="TEST")).values

            assert len(result) == 1
            assert result[0].id == "1"

    async def test_get_comment_templates_of_missing_queue(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/NOPE/commentTemplates?page=1&perPage=50",
                status=404,
            )

            with pytest.raises(QueueNotFound) as exc_info:
                await tracker_client.get_comment_templates(queue="NOPE")

            assert exc_info.value.queue_id == "NOPE"

    async def test_get_comment_template_success(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates/1",
                payload=sample_template_data,
            )

            result = await tracker_client.get_comment_template("1")

            assert isinstance(result, CommentTemplate)
            assert result.id == "1"
            assert result.version == 2
            assert result.name == "Incident acknowledged"

    async def test_get_comment_template_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_template_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_template_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates/1",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.get_comment_template(
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

    async def test_get_comment_template_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates/missing",
                status=404,
            )

            with pytest.raises(CommentTemplateNotFound) as exc_info:
                await tracker_client.get_comment_template("missing")

            assert exc_info.value.template_id == "missing"

    async def test_undocumented_fields_are_preserved(
        self, tracker_client: TrackerClient, sample_template_data: dict[str, Any]
    ) -> None:
        """The endpoint is not in the public API reference, so unknown keys must
        reach the caller rather than being dropped by the model."""
        payload = {**sample_template_data, "someUndocumentedField": {"nested": 1}}

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/commentTemplates/1", payload=payload
            )

            result = await tracker_client.get_comment_template("1")

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
                "https://api.tracker.yandex.net/v3/commentTemplates?page=1&perPage=50",
                payload=[{"id": template_id, "name": "Template"}],
            )

            result = (await tracker_client.get_comment_templates()).values

            assert result[0].id == template_id
