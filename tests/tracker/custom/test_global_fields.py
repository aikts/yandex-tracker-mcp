from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import GlobalField
from tests.aioresponses_utils import RequestCapture


class TestGlobalFields:
    @pytest.fixture
    def sample_global_field_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/fields/summary",
            "id": "summary",
            "version": 1,
            "name": "Summary",
            "description": "Issue summary",
            "key": "summary",
            "readonly": False,
            "options": False,
            "suggest": True,
            "queryProvider": {"type": "StringOptionalQueryProvider"},
            "order": 1,
            "category": {
                "self": "https://api.tracker.yandex.net/v3/fields/categories/000000000000000000000001",
                "id": "000000000000000000000001",
                "display": "System",
            },
            "type": "ru.yandex.startrek.core.fields.StringFieldType",
        }

    async def test_get_global_fields_success(
        self, tracker_client: TrackerClient, sample_global_field_data: dict[str, Any]
    ) -> None:
        fields_response = [sample_global_field_data]

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", payload=fields_response)

            result = await tracker_client.get_global_fields()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], GlobalField)
            assert result[0].key == "summary"
            assert result[0].readonly is False
            assert result[0].options is False
            assert result[0].suggest is True

    async def test_get_global_fields_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_global_field_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        fields_response = [sample_global_field_data]
        capture = RequestCapture(payload=fields_response)

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", callback=capture.callback)

            result = await tracker_client_no_org.get_global_fields(
                auth=yandex_auth_cloud
            )

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_get_global_fields_multiple(
        self, tracker_client: TrackerClient
    ) -> None:
        field1_data = {
            "self": "https://api.tracker.yandex.net/v3/fields/summary",
            "id": "summary",
            "version": 1,
            "name": "Summary",
            "description": "Issue summary",
            "key": "summary",
            "readonly": False,
            "options": False,
            "suggest": True,
            "queryProvider": {"type": "StringOptionalQueryProvider"},
            "order": 1,
            "category": {
                "self": "https://api.tracker.yandex.net/v3/fields/categories/000000000000000000000001",
                "id": "000000000000000000000001",
                "display": "System",
            },
            "type": "ru.yandex.startrek.core.fields.StringFieldType",
        }

        field2_data = {
            "self": "https://api.tracker.yandex.net/v3/fields/description",
            "id": "description",
            "version": 1,
            "name": "Description",
            "description": "Issue description",
            "key": "description",
            "readonly": False,
            "options": False,
            "suggest": False,
            "queryProvider": {"type": "StringOptionalQueryProvider"},
            "order": 2,
            "category": {
                "self": "https://api.tracker.yandex.net/v3/fields/categories/000000000000000000000001",
                "id": "000000000000000000000001",
                "display": "System",
            },
            "type": "ru.yandex.startrek.core.fields.TextFieldType",
        }

        fields_response = [field1_data, field2_data]

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", payload=fields_response)

            result = await tracker_client.get_global_fields()

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(field, GlobalField) for field in result)
            assert result[0].key == "summary"
            assert result[1].key == "description"

    async def test_get_global_fields_empty(self, tracker_client: TrackerClient) -> None:
        fields_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", payload=fields_response)

            result = await tracker_client.get_global_fields()

            assert isinstance(result, list)
            assert len(result) == 0
