import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from pytest_mock import MockerFixture
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest

from mcp_tracker.tracker.custom.client import (
    IAMTokenInfo,
    ServiceAccountSettings,
    ServiceAccountStore,
)


class TestServiceAccountSettings:
    def test_init(self):
        settings = ServiceAccountSettings(
            key_id="test-key-id",
            service_account_id="test-sa-id",
            private_key="test-private-key",
        )

        assert settings.key_id == "test-key-id"
        assert settings.service_account_id == "test-sa-id"
        assert settings.private_key == "test-private-key"

    def test_to_yandexcloud_dict(self):
        settings = ServiceAccountSettings(
            key_id="test-key-id",
            service_account_id="test-sa-id",
            private_key="test-private-key",
        )

        result = settings.to_yandexcloud_dict()

        expected = {
            "id": "test-key-id",
            "service_account_id": "test-sa-id",
            "private_key": "test-private-key",
        }
        assert result == expected


class TestIAMTokenInfo:
    def test_init(self):
        token_info = IAMTokenInfo(token="test-token")
        assert token_info.token == "test-token"


class TestServiceAccountStore:
    @pytest.fixture
    def mock_settings(self) -> ServiceAccountSettings:
        return ServiceAccountSettings(
            key_id="test-key-id",
            service_account_id="test-sa-id",
            private_key="-----BEGIN PRIVATE KEY-----\ntest-private-key\n-----END PRIVATE KEY-----",
        )

    @pytest.fixture
    def mock_iam_service(self, mocker: MockerFixture) -> Any:
        mock_service = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.iam_token = "test-iam-token"
        mock_service.Create.return_value = mock_response
        return mock_service

    def test_init(self, mock_settings: ServiceAccountSettings, mocker: MockerFixture):
        # Mock the yandexcloud SDK at import level
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_iam_service = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)

        mock_sdk_class.assert_called_once_with(
            service_account_key=mock_settings.to_yandexcloud_dict()
        )
        mock_sdk.client.assert_called_once()
        assert isinstance(store._executor, ThreadPoolExecutor)
        assert store._iam_token is None
        assert isinstance(store._lock, asyncio.Lock)
        assert store._refresh_task is None

    async def test_prepare_starts_refresh_task(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_iam_service = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)

        await store.prepare()

        assert store._refresh_task is not None
        assert not store._refresh_task.done()

        # Cleanup
        store._refresh_task.cancel()
        try:
            await store._refresh_task
        except asyncio.CancelledError:
            pass

    async def test_close_cancels_refresh_task(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_iam_service = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)
        await store.prepare()

        assert store._refresh_task is not None
        assert not store._refresh_task.done()

        # Close should handle the cancellation gracefully
        await store.close()

        # The task should be cancelled but may not be set to None due to CancelledError handling
        assert store._refresh_task is not None
        assert store._refresh_task.cancelled()

    async def test_get_iam_token_first_call(
        self,
        mock_settings: ServiceAccountSettings,
        mock_iam_service: Any,
        mocker: MockerFixture,
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_jwt_encode = mocker.patch("jwt.encode")
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk
        mock_jwt_encode.return_value = "test-jwt-token"

        store = ServiceAccountStore(mock_settings)

        mock_fetch = mocker.patch.object(
            store, "_fetch_iam_token", return_value=IAMTokenInfo(token="test-token")
        )
        token = await store.get_iam_token()

        assert token == "test-token"
        assert store._iam_token is not None
        assert store._iam_token.token == "test-token"
        mock_fetch.assert_called_once_with(mock_settings)

    async def test_get_iam_token_cached(
        self,
        mock_settings: ServiceAccountSettings,
        mock_iam_service: Any,
        mocker: MockerFixture,
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)
        store._iam_token = IAMTokenInfo(token="cached-token")

        token = await store.get_iam_token()

        assert token == "cached-token"

    async def test_get_iam_token_force_refresh(
        self,
        mock_settings: ServiceAccountSettings,
        mock_iam_service: Any,
        mocker: MockerFixture,
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)
        store._iam_token = IAMTokenInfo(token="old-token")

        mock_fetch = mocker.patch.object(
            store, "_fetch_iam_token", return_value=IAMTokenInfo(token="new-token")
        )
        token = await store.get_iam_token(force_refresh=True)

        assert token == "new-token"
        assert store._iam_token.token == "new-token"
        mock_fetch.assert_called_once_with(mock_settings)

    def test_fetch_iam_token(
        self,
        mock_settings: ServiceAccountSettings,
        mock_iam_service: Any,
        mocker: MockerFixture,
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_jwt_encode = mocker.patch("jwt.encode")
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk
        mock_jwt_encode.return_value = "test-jwt-token"

        store = ServiceAccountStore(mock_settings)

        mocker.patch("time.time", return_value=1000)
        result = store._fetch_iam_token(mock_settings)

        assert isinstance(result, IAMTokenInfo)
        assert result.token == "test-iam-token"

        # Verify JWT token creation
        mock_jwt_encode.assert_called_once_with(
            payload={
                "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                "iss": "test-sa-id",
                "iat": 1000,
                "exp": 4600,
            },
            key="-----BEGIN PRIVATE KEY-----\ntest-private-key\n-----END PRIVATE KEY-----",
            algorithm="PS256",
            headers={"kid": "test-key-id"},
        )

        # Verify IAM service call
        mock_iam_service.Create.assert_called_once()
        call_args = mock_iam_service.Create.call_args[0][0]
        assert isinstance(call_args, CreateIamTokenRequest)
        assert call_args.jwt == "test-jwt-token"

    async def test_concurrent_token_requests(
        self,
        mock_settings: ServiceAccountSettings,
        mock_iam_service: Any,
        mocker: MockerFixture,
    ):
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mock_iam_service
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)

        fetch_call_count = 0

        def mock_fetch(*_args: Any) -> IAMTokenInfo:
            nonlocal fetch_call_count
            fetch_call_count += 1
            # Simulate synchronous work (since _fetch_iam_token is sync)
            return IAMTokenInfo(token=f"token-{fetch_call_count}")

        mocker.patch.object(store, "_fetch_iam_token", side_effect=mock_fetch)
        # Start multiple concurrent requests
        tasks = [store.get_iam_token() for _ in range(3)]
        tokens = await asyncio.gather(*tasks)

        # All should get the same token (only one fetch should happen)
        assert all(token == tokens[0] for token in tokens)
        assert fetch_call_count == 1
