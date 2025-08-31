import pytest
from aiohttp import ClientSession
from pytest_mock import MockerFixture

from mcp_tracker.tracker.custom.client import (
    ServiceAccountSettings,
    ServiceAccountStore,
    TrackerClient,
)
from mcp_tracker.tracker.proto.common import YandexAuth


class TestTrackerClientInit:
    async def test_init_with_oauth_token(self):
        client = TrackerClient(
            token="test-oauth-token",
            org_id="test-org-123",
            base_url="https://api.test.com",
            timeout=5.0,
        )
        await client.close()

        assert client._token == "test-oauth-token"
        assert client._static_iam_token is None
        assert client._service_account_store is None
        assert client._org_id == "test-org-123"
        assert client._cloud_org_id is None

    async def test_init_with_iam_token(self):
        client = TrackerClient(
            token=None, iam_token="test-iam-token", cloud_org_id="cloud-org-456"
        )
        await client.close()

        assert client._token is None
        assert client._static_iam_token == "test-iam-token"
        assert client._service_account_store is None
        assert client._cloud_org_id == "cloud-org-456"
        assert client._org_id is None

    async def test_init_with_service_account(self, mocker: MockerFixture):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk
        service_account = ServiceAccountSettings(
            key_id="key-id",
            service_account_id="sa-id",
            private_key="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC8Q7HgL\n-----END PRIVATE KEY-----",
        )

        client = TrackerClient(
            token=None, service_account=service_account, org_id="test-org"
        )

        assert client._token is None
        assert client._static_iam_token is None
        assert isinstance(client._service_account_store, ServiceAccountStore)
        assert client._org_id == "test-org"
        await client.close()

    async def test_prepare_with_service_account(self, mocker: MockerFixture):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk
        service_account = ServiceAccountSettings(
            key_id="key-id",
            service_account_id="sa-id",
            private_key="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC8Q7HgL\n-----END PRIVATE KEY-----",
        )

        mock_prepare = mocker.patch.object(ServiceAccountStore, "prepare")
        client = TrackerClient(
            token=None, service_account=service_account, org_id="test-org"
        )

        await client.prepare()
        mock_prepare.assert_called_once()
        await client.close()

    async def test_prepare_without_service_account(self):
        client = TrackerClient(token="test-token", org_id="test-org")

        # Should not raise any exceptions
        await client.prepare()
        await client.close()

    async def test_close_with_service_account(self, mocker: MockerFixture):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk
        service_account = ServiceAccountSettings(
            key_id="key-id",
            service_account_id="sa-id",
            private_key="-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC8Q7HgL\n-----END PRIVATE KEY-----",
        )

        mock_close = mocker.patch.object(ServiceAccountStore, "close")
        mock_session_close = mocker.patch.object(ClientSession, "close")

        client = TrackerClient(
            token=None, service_account=service_account, org_id="test-org"
        )

        await client.close()
        mock_close.assert_called_once()
        mock_session_close.assert_called_once()


class TestOAuthAuthentication:
    async def test_build_headers_oauth_from_auth_param(self):
        client = TrackerClient(token="static-oauth-token", org_id="static-org")

        auth = YandexAuth(token="dynamic-oauth-token", org_id="dynamic-org")

        headers = await client._build_headers(auth)

        expected = {
            "Authorization": "OAuth dynamic-oauth-token",
            "X-Org-ID": "dynamic-org",
        }
        assert headers == expected

    async def test_build_headers_oauth_static_token(self):
        client = TrackerClient(token="static-oauth-token", org_id="test-org")

        headers = await client._build_headers()

        expected = {"Authorization": "OAuth static-oauth-token", "X-Org-ID": "test-org"}
        assert headers == expected

    async def test_build_headers_oauth_with_cloud_org_id(self):
        client = TrackerClient(token="oauth-token", cloud_org_id="cloud-org-123")

        headers = await client._build_headers()

        expected = {
            "Authorization": "OAuth oauth-token",
            "X-Cloud-Org-ID": "cloud-org-123",
        }
        assert headers == expected


class TestIAMAuthentication:
    async def test_build_headers_static_iam_token(self):
        client = TrackerClient(
            token=None, iam_token="static-iam-token", org_id="test-org"
        )

        headers = await client._build_headers()

        expected = {"Authorization": "Bearer static-iam-token", "X-Org-ID": "test-org"}
        assert headers == expected

    async def test_build_headers_service_account_iam(self, mocker: MockerFixture):
        service_account = ServiceAccountSettings(
            key_id="key-id", service_account_id="sa-id", private_key="private-key"
        )

        mock_store = mocker.Mock(spec=ServiceAccountStore)
        mock_store.get_iam_token = mocker.AsyncMock(return_value="dynamic-iam-token")

        # Mock the yandexcloud.SDK to avoid real initialization
        mocker.patch("mcp_tracker.tracker.custom.client.yandexcloud.SDK")

        # Create client and replace the store after initialization
        client = TrackerClient(
            token=None, service_account=service_account, org_id="test-org"
        )
        client._service_account_store = mock_store

        headers = await client._build_headers()

        expected = {
            "Authorization": "Bearer dynamic-iam-token",
            "X-Org-ID": "test-org",
        }
        assert headers == expected
        mock_store.get_iam_token.assert_called_once()


class TestAuthenticationPriority:
    async def test_auth_priority_oauth_param_wins(self, mocker: MockerFixture):
        service_account = ServiceAccountSettings(
            key_id="key-id", service_account_id="sa-id", private_key="private-key"
        )

        mock_store = mocker.Mock(spec=ServiceAccountStore)
        mock_store.get_iam_token = mocker.AsyncMock(return_value="sa-iam-token")

        # Mock the yandexcloud.SDK to avoid real initialization
        mocker.patch("mcp_tracker.tracker.custom.client.yandexcloud.SDK")

        # Create client and replace the store after initialization
        client = TrackerClient(
            token="static-oauth",
            iam_token="static-iam",
            service_account=service_account,
            org_id="test-org",
        )
        client._service_account_store = mock_store

        auth = YandexAuth(token="dynamic-oauth", org_id="test-org")
        headers = await client._build_headers(auth)

        assert headers["Authorization"] == "OAuth dynamic-oauth"
        mock_store.get_iam_token.assert_not_called()

    async def test_auth_priority_static_oauth_over_iam(self, mocker: MockerFixture):
        service_account = ServiceAccountSettings(
            key_id="key-id", service_account_id="sa-id", private_key="private-key"
        )

        mock_store = mocker.Mock(spec=ServiceAccountStore)
        mock_store.get_iam_token = mocker.AsyncMock(return_value="sa-iam-token")

        # Mock the yandexcloud.SDK to avoid real initialization
        mocker.patch("mcp_tracker.tracker.custom.client.yandexcloud.SDK")

        # Create client and replace the store after initialization
        client = TrackerClient(
            token="static-oauth",
            iam_token="static-iam",
            service_account=service_account,
            org_id="test-org",
        )
        client._service_account_store = mock_store

        headers = await client._build_headers()

        assert headers["Authorization"] == "OAuth static-oauth"
        mock_store.get_iam_token.assert_not_called()

    async def test_auth_priority_static_iam_over_service_account(
        self, mocker: MockerFixture
    ):
        service_account = ServiceAccountSettings(
            key_id="key-id", service_account_id="sa-id", private_key="private-key"
        )

        mock_store = mocker.Mock(spec=ServiceAccountStore)
        mock_store.get_iam_token = mocker.AsyncMock(return_value="sa-iam-token")

        # Mock the yandexcloud.SDK to avoid real initialization
        mocker.patch("mcp_tracker.tracker.custom.client.yandexcloud.SDK")

        # Create client and replace the store after initialization
        client = TrackerClient(
            token=None,
            iam_token="static-iam",
            service_account=service_account,
            org_id="test-org",
        )
        client._service_account_store = mock_store

        headers = await client._build_headers()

        assert headers["Authorization"] == "Bearer static-iam"
        mock_store.get_iam_token.assert_not_called()

    async def test_no_auth_provided_raises_error(self):
        client = TrackerClient(
            token=None, iam_token=None, service_account=None, org_id="test-org"
        )

        with pytest.raises(ValueError, match="No authentication method provided"):
            await client._build_headers()


class TestOrganizationHandling:
    async def test_auth_org_id_overrides_client_org_id(self):
        client = TrackerClient(token="test-token", org_id="client-org")

        auth = YandexAuth(token="auth-token", org_id="auth-org")
        headers = await client._build_headers(auth)

        assert headers["X-Org-ID"] == "auth-org"

    async def test_auth_cloud_org_id_overrides_client_cloud_org_id(self):
        client = TrackerClient(token="test-token", cloud_org_id="client-cloud-org")

        auth = YandexAuth(token="auth-token", cloud_org_id="auth-cloud-org")
        headers = await client._build_headers(auth)

        assert headers["X-Cloud-Org-ID"] == "auth-cloud-org"

    async def test_both_org_ids_provided_raises_error(self):
        client = TrackerClient(
            token="test-token", org_id="test-org", cloud_org_id="test-cloud-org"
        )

        with pytest.raises(
            ValueError, match="Only one of org_id or cloud_org_id should be provided"
        ):
            await client._build_headers()

    async def test_auth_both_org_ids_provided_raises_error(self):
        client = TrackerClient(token="test-token", org_id="client-org")

        auth = YandexAuth(
            token="auth-token", org_id="auth-org", cloud_org_id="auth-cloud-org"
        )

        with pytest.raises(
            ValueError, match="Only one of org_id or cloud_org_id should be provided"
        ):
            await client._build_headers(auth)

    async def test_no_org_id_provided_raises_error(self):
        client = TrackerClient(token="test-token")

        with pytest.raises(
            ValueError, match="Either org_id or cloud_org_id must be provided"
        ):
            await client._build_headers()
