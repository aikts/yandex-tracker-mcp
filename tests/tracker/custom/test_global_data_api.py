import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import GlobalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.statuses import Status


class TestGlobalDataAPI:
    @pytest.fixture
    async def client(self):
        client = TrackerClient(
            token="test-token",
            org_id="test-org",
            base_url="https://api.tracker.yandex.net",
        )
        yield client
        await client.close()

    @pytest.fixture
    async def client_no_org(self):
        client = TrackerClient(
            token="test-token",
            base_url="https://api.tracker.yandex.net",
        )
        yield client
        await client.close()

    @pytest.fixture
    def sample_global_field_data(self):
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

    @pytest.fixture
    def sample_status_data(self):
        return {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "version": 1,
            "key": "open",
            "name": "Open",
            "order": 1,
            "type": "new",
            "statusType": {
                "self": "https://api.tracker.yandex.net/v3/statusTypes/1",
                "id": "1",
                "key": "new",
                "display": "New",
            },
        }

    @pytest.fixture
    def sample_issue_type_data(self):
        return {
            "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
            "id": "1",
            "version": 1,
            "key": "task",
            "name": "Task",
            "description": "General task",
        }

    @pytest.fixture
    def sample_priority_data(self):
        return {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "version": 1,
            "key": "normal",
            "name": "Normal",
            "order": 2,
        }

    async def test_get_global_fields_success(self, client, sample_global_field_data):
        fields_response = [sample_global_field_data]

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", payload=fields_response)

            result = await client.get_global_fields()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], GlobalField)
            assert result[0].key == "summary"
            assert result[0].readonly is False
            assert result[0].options is False
            assert result[0].suggest is True

    async def test_get_global_fields_with_auth(
        self, client_no_org, sample_global_field_data
    ):
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")
        fields_response = [sample_global_field_data]

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", payload=fields_response)

            result = await client_no_org.get_global_fields(auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"

    async def test_get_global_fields_multiple(self, client):
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

            result = await client.get_global_fields()

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(field, GlobalField) for field in result)
            assert result[0].key == "summary"
            assert result[1].key == "description"

    async def test_get_statuses_success(self, client, sample_status_data):
        statuses_response = [sample_status_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/statuses", payload=statuses_response
            )

            result = await client.get_statuses()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Status)
            assert result[0].key == "open"
            assert result[0].name == "Open"

    async def test_get_statuses_with_auth(self, client, sample_status_data):
        auth = YandexAuth(token="auth-token", org_id="auth-org")
        statuses_response = [sample_status_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/statuses", payload=statuses_response
            )

            result = await client.get_statuses(auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Org-ID"] == "auth-org"

    async def test_get_issue_types_success(self, client, sample_issue_type_data):
        types_response = [sample_issue_type_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issuetypes", payload=types_response
            )

            result = await client.get_issue_types()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueType)
            assert result[0].key == "task"
            assert result[0].name == "Task"

    async def test_get_issue_types_with_auth(
        self, client_no_org, sample_issue_type_data
    ):
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")
        types_response = [sample_issue_type_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issuetypes", payload=types_response
            )

            result = await client_no_org.get_issue_types(auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"

    async def test_get_priorities_success(self, client, sample_priority_data):
        priorities_response = [sample_priority_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await client.get_priorities()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Priority)
            assert result[0].key == "normal"
            assert result[0].name == "Normal"
            assert result[0].order == 2

    async def test_get_priorities_with_auth(self, client_no_org, sample_priority_data):
        auth = YandexAuth(token="auth-token", org_id="auth-org")
        priorities_response = [sample_priority_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await client_no_org.get_priorities(auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Org-ID"] == "auth-org"

    async def test_get_priorities_multiple_with_order(self, client):
        priority1_data = {
            "self": "https://api.tracker.yandex.net/v3/priorities/1",
            "id": "1",
            "version": 1,
            "key": "trivial",
            "name": "Trivial",
            "order": 1,
        }

        priority2_data = {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "version": 1,
            "key": "normal",
            "name": "Normal",
            "order": 2,
        }

        priority3_data = {
            "self": "https://api.tracker.yandex.net/v3/priorities/3",
            "id": "3",
            "version": 1,
            "key": "critical",
            "name": "Critical",
            "order": 3,
        }

        priorities_response = [priority1_data, priority2_data, priority3_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await client.get_priorities()

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(isinstance(priority, Priority) for priority in result)

            # Check priorities in order
            assert result[0].key == "trivial"
            assert result[0].order == 1
            assert result[1].key == "normal"
            assert result[1].order == 2
            assert result[2].key == "critical"
            assert result[2].order == 3

    async def test_get_global_fields_empty(self, client):
        fields_response: list[dict] = []

        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/fields", payload=fields_response)

            result = await client.get_global_fields()

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_get_statuses_empty(self, client):
        statuses_response: list[dict] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/statuses", payload=statuses_response
            )

            result = await client.get_statuses()

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_get_issue_types_empty(self, client):
        types_response: list[dict] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issuetypes", payload=types_response
            )

            result = await client.get_issue_types()

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_get_priorities_empty(self, client):
        priorities_response: list[dict] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/priorities",
                payload=priorities_response,
            )

            result = await client.get_priorities()

            assert isinstance(result, list)
            assert len(result) == 0
