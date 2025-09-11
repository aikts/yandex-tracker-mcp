from typing import Any, AsyncGenerator, Dict

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import LocalField
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion


class TestQueuesAPI:
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
    def sample_queue_data(self) -> Dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST",
            "id": 123,
            "key": "TEST",
            "version": 1,
            "name": "Test Queue",
            "description": "A test queue for testing purposes",
            "lead": {
                "self": "https://api.tracker.yandex.net/v3/users/1234567890",
                "id": "user123",
                "display": "Queue Lead",
            },
            "assignAuto": False,
            "defaultType": {
                "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
                "id": "1",
                "key": "task",
                "display": "Task",
            },
            "defaultPriority": {
                "self": "https://api.tracker.yandex.net/v3/priorities/2",
                "id": "2",
                "key": "normal",
                "display": "Normal",
            },
        }

    @pytest.fixture
    def sample_local_field_data(self):
        return {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST/localFields/customField1",
            "id": "local-field-123",
            "key": "customField1",
            "version": 1,
            "name": "Custom Field",
            "description": "A custom field for testing",
            "readonly": False,
            "options": True,
            "suggest": False,
            "queryProvider": {"type": "StringOptionalQueryProvider"},
            "order": 1,
            "category": {
                "self": "https://api.tracker.yandex.net/v3/fields/categories/000000000000000000000001",
                "id": "000000000000000000000001",
                "display": "System",
            },
            "type": "ru.yandex.startrek.core.fields.StringFieldType",
        }

    @pytest.fixture
    def sample_version_data(self) -> Dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST/versions/1",
            "id": 123,
            "version": 1,
            "name": "1.0.0",
            "description": "Initial release",
            "startDate": "2023-01-01",
            "dueDate": "2023-12-31",
            "released": False,
            "archived": False,
        }

    async def test_queues_list_success(
        self, client: TrackerClient, sample_queue_data: Dict[str, Any]
    ):
        queues_response = [sample_queue_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues?page=1&perPage=100",
                payload=queues_response,
            )

            result = await client.queues_list()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Queue)
            assert result[0].key == "TEST"
            assert result[0].name == "Test Queue"
            assert result[0].description == "A test queue for testing purposes"

    async def test_queues_list_with_pagination(
        self, client: TrackerClient, sample_queue_data: Dict[str, Any]
    ):
        queues_response = [sample_queue_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues?page=2&perPage=50",
                payload=queues_response,
            )

            result = await client.queues_list(per_page=50, page=2)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify request parameters
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["params"]["perPage"] == 50
            assert request.kwargs["params"]["page"] == 2

    async def test_queues_list_with_auth(
        self, client_no_org: TrackerClient, sample_queue_data: Dict[str, Any]
    ):
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")
        queues_response = [sample_queue_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues?page=1&perPage=100",
                payload=queues_response,
            )

            result = await client_no_org.queues_list(auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"

    async def test_queues_get_local_fields_success(
        self, client: TrackerClient, sample_local_field_data: Dict[str, Any]
    ):
        fields_response = [sample_local_field_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/localFields",
                payload=fields_response,
            )

            result = await client.queues_get_local_fields("TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], LocalField)
            assert result[0].key == "customField1"

    async def test_queues_get_local_fields_with_auth(
        self, client: TrackerClient, sample_local_field_data: Dict[str, Any]
    ):
        auth = YandexAuth(token="auth-token", org_id="auth-org")
        fields_response = [sample_local_field_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/PROJ/localFields",
                payload=fields_response,
            )

            result = await client.queues_get_local_fields("PROJ", auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Org-ID"] == "auth-org"

    async def test_queues_get_tags_success(self, client):
        tags_response: list[str] = ["bug", "feature", "improvement", "task"]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/tags",
                payload=tags_response,
            )

            result = await client.queues_get_tags("TEST")

            assert isinstance(result, list)
            assert len(result) == 4
            assert all(isinstance(tag, str) for tag in result)
            assert "bug" in result
            assert "feature" in result
            assert "improvement" in result
            assert "task" in result

    async def test_queues_get_tags_empty(self, client):
        tags_response: list[str] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/EMPTY/tags",
                payload=tags_response,
            )

            result = await client.queues_get_tags("EMPTY")

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_queues_get_tags_with_auth(self, client):
        auth = YandexAuth(token="auth-token", org_id="auth-org")
        tags_response = ["urgent", "documentation"]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/DOC/tags",
                payload=tags_response,
            )

            result = await client.queues_get_tags("DOC", auth=auth)

            assert isinstance(result, list)
            assert len(result) == 2
            assert "urgent" in result
            assert "documentation" in result

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Org-ID"] == "auth-org"

    async def test_queues_get_versions_success(self, client, sample_version_data):
        versions_response = [sample_version_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/versions",
                payload=versions_response,
            )

            result = await client.queues_get_versions("TEST")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], QueueVersion)
            assert result[0].name == "1.0.0"
            assert result[0].description == "Initial release"
            assert result[0].released is False
            assert result[0].archived is False

    async def test_queues_get_versions_multiple(self, client):
        version1_data = {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST/versions/1",
            "id": 123,
            "version": 1,
            "name": "1.0.0",
            "description": "Initial release",
            "startDate": "2023-01-01",
            "dueDate": "2023-06-30",
            "released": True,
            "archived": False,
        }

        version2_data = {
            "self": "https://api.tracker.yandex.net/v3/queues/TEST/versions/2",
            "id": 456,
            "version": 2,
            "name": "2.0.0",
            "description": "Major update",
            "startDate": "2023-07-01",
            "dueDate": "2023-12-31",
            "released": False,
            "archived": False,
        }

        versions_response = [version1_data, version2_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/versions",
                payload=versions_response,
            )

            result = await client.queues_get_versions("TEST")

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(version, QueueVersion) for version in result)

            # Check first version
            assert result[0].name == "1.0.0"
            assert result[0].released is True

            # Check second version
            assert result[1].name == "2.0.0"
            assert result[1].released is False

    async def test_queues_get_versions_with_auth(
        self, client_no_org, sample_version_data
    ):
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")
        versions_response = [sample_version_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/PROJ/versions",
                payload=versions_response,
            )

            result = await client_no_org.queues_get_versions("PROJ", auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"

    async def test_queues_get_versions_empty(self, client):
        versions_response: list[dict] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/NOVERSIONS/versions",
                payload=versions_response,
            )

            result = await client.queues_get_versions("NOVERSIONS")

            assert isinstance(result, list)
            assert len(result) == 0
