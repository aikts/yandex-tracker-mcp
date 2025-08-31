from aiohttp import ClientSession
from pytest_mock import MockerFixture

from mcp_tracker.tracker.custom.client import (
    ServiceAccountSettings,
    ServiceAccountStore,
    TrackerClient,
)


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
