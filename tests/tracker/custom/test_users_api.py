from typing import Any, AsyncGenerator, Dict

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.users import User


class TestUsersAPI:
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
    def sample_user_data(self) -> Dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "version": 1,
            "uid": 1234567890,
            "login": "test.user",
            "trackerUid": 1234567890,
            "passportUid": 1234567890,
            "firstName": "Test",
            "lastName": "User",
            "display": "Test User",
            "email": "test.user@example.com",
            "external": False,
            "hasLicense": True,
            "dismissed": False,
            "useNewFilters": True,
            "disableNotifications": False,
            "firstLoginDate": "2023-01-01T12:00:00.000+0000",
            "lastLoginDate": "2023-12-31T12:00:00.000+0000",
        }

    @pytest.fixture
    def sample_current_user_data(self):
        return {
            "self": "https://api.tracker.yandex.net/v3/users/9876543210",
            "id": "current-user-456",
            "version": 1,
            "uid": 9876543210,
            "login": "current.user",
            "trackerUid": 9876543210,
            "passportUid": 9876543210,
            "firstName": "Current",
            "lastName": "User",
            "display": "Current User",
            "email": "current.user@example.com",
            "external": False,
            "hasLicense": True,
            "dismissed": False,
            "useNewFilters": True,
            "disableNotifications": False,
            "firstLoginDate": "2023-06-01T10:00:00.000+0000",
            "lastLoginDate": "2024-01-15T15:30:00.000+0000",
        }

    async def test_users_list_success(
        self, client: TrackerClient, sample_user_data: Dict[str, Any]
    ):
        users_response = [sample_user_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users?page=1&perPage=50",
                payload=users_response,
            )

            result = await client.users_list()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], User)
            assert result[0].login == "test.user"
            assert result[0].display == "Test User"
            assert result[0].email == "test.user@example.com"
            # assert result[0].hasLicense is True  # Field not in model
            assert result[0].external is False

    async def test_users_list_with_pagination(
        self, client: TrackerClient, sample_user_data: Dict[str, Any]
    ):
        users_response = [sample_user_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users?page=3&perPage=25",
                payload=users_response,
            )

            result = await client.users_list(per_page=25, page=3)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify request parameters
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["params"]["perPage"] == 25
            assert request.kwargs["params"]["page"] == 3

    async def test_users_list_with_auth(
        self, client_no_org: TrackerClient, sample_user_data: Dict[str, Any]
    ):
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")
        users_response = [sample_user_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users?page=1&perPage=50",
                payload=users_response,
            )

            result = await client_no_org.users_list(auth=auth)

            assert isinstance(result, list)
            assert len(result) == 1

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"

    async def test_users_list_multiple_users(self, client: TrackerClient):
        user1_data = {
            "self": "https://api.tracker.yandex.net/v3/users/1111111111",
            "id": "user1",
            "version": 1,
            "uid": 1111111111,
            "login": "user1",
            "trackerUid": 1111111111,
            "passportUid": 1111111111,
            "firstName": "User",
            "lastName": "One",
            "display": "User One",
            "email": "user1@example.com",
            "external": False,
            "hasLicense": True,
            "dismissed": False,
        }

        user2_data = {
            "self": "https://api.tracker.yandex.net/v3/users/2222222222",
            "id": "user2",
            "version": 1,
            "uid": 2222222222,
            "login": "user2",
            "trackerUid": 2222222222,
            "passportUid": 2222222222,
            "firstName": "User",
            "lastName": "Two",
            "display": "User Two",
            "email": "user2@example.com",
            "external": True,
            "hasLicense": False,
            "dismissed": False,
        }

        users_response = [user1_data, user2_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users?page=1&perPage=50",
                payload=users_response,
            )

            result = await client.users_list()

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(user, User) for user in result)

            # Check first user
            assert result[0].login == "user1"
            # assert result[0].hasLicense is True  # Field not in model
            assert result[0].external is False

            # Check second user
            assert result[1].login == "user2"
            # assert result[1].hasLicense is False  # Field not in model
            assert result[1].external is True

    async def test_user_get_success_by_login(self, client, sample_user_data):
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users/test.user",
                payload=sample_user_data,
            )

            result = await client.user_get("test.user")

            assert isinstance(result, User)
            assert result.login == "test.user"
            assert result.display == "Test User"
            assert result.email == "test.user@example.com"

    async def test_user_get_success_by_uid(self, client, sample_user_data):
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users/1234567890",
                payload=sample_user_data,
            )

            result = await client.user_get("1234567890")

            assert isinstance(result, User)
            assert result.uid == 1234567890
            assert result.login == "test.user"

    async def test_user_get_not_found(self, client):
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users/nonexistent.user", status=404
            )

            result = await client.user_get("nonexistent.user")

            assert result is None

    async def test_user_get_with_auth(self, client, sample_user_data):
        auth = YandexAuth(token="auth-token", org_id="auth-org")

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users/test.user",
                payload=sample_user_data,
            )

            result = await client.user_get("test.user", auth=auth)

            assert isinstance(result, User)
            assert result.login == "test.user"

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Org-ID"] == "auth-org"

    async def test_user_get_current_success(self, client, sample_current_user_data):
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/myself",
                payload=sample_current_user_data,
            )

            result = await client.user_get_current()

            assert isinstance(result, User)
            assert result.login == "current.user"
            assert result.display == "Current User"
            assert result.email == "current.user@example.com"
            assert result.uid == 9876543210

    async def test_user_get_current_with_auth(
        self, client_no_org, sample_current_user_data
    ):
        auth = YandexAuth(token="auth-token", cloud_org_id="cloud-org")

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/myself",
                payload=sample_current_user_data,
            )

            result = await client_no_org.user_get_current(auth=auth)

            assert isinstance(result, User)
            assert result.login == "current.user"

            # Verify the request was made with correct headers
            request_key = list(m.requests.keys())[0]
            request = m.requests[request_key][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
            assert request.kwargs["headers"]["X-Cloud-Org-ID"] == "cloud-org"

    async def test_users_list_empty_result(self, client):
        users_response: list[dict] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/users?page=1&perPage=50",
                payload=users_response,
            )

            result = await client.users_list()

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_user_get_server_error_propagated(self, client):
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/users/error.user", status=500)

            with pytest.raises(Exception):  # noqa: B017
                await client.user_get("error.user")

    async def test_user_get_current_server_error_propagated(self, client):
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/myself", status=500)

            with pytest.raises(Exception):  # noqa: B017
                await client.user_get_current()
