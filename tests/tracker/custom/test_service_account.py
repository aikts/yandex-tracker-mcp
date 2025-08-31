import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest

from mcp_tracker.tracker.custom.client import (
    IAMTokenInfo,
    ServiceAccountSettings,
    ServiceAccountStore,
)


class TestServiceAccountSettings:
    def test_init(self) -> None:
        settings = ServiceAccountSettings(
            key_id="test-key-id",
            service_account_id="test-sa-id",
            private_key="test-private-key",
        )

        assert settings.key_id == "test-key-id"
        assert settings.service_account_id == "test-sa-id"
        assert settings.private_key == "test-private-key"

    def test_to_yandexcloud_dict(self) -> None:
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
    def test_init(self) -> None:
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

    def test_init(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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
    ) -> None:
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

    def test_init_with_custom_refresh_interval(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        custom_interval = 60.0
        store = ServiceAccountStore(mock_settings, refresh_interval=custom_interval)

        assert store._refresh_interval == custom_interval

    def test_init_uses_default_refresh_interval(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)

        assert store._refresh_interval == ServiceAccountStore.DEFAULT_REFRESH_INTERVAL

    def test_init_with_custom_retry_interval(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        custom_retry = 5.0
        store = ServiceAccountStore(mock_settings, retry_interval=custom_retry)

        assert store._retry_interval == custom_retry

    def test_init_uses_default_retry_interval(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(mock_settings)

        assert store._retry_interval == ServiceAccountStore.DEFAULT_RETRY_INTERVAL

    async def test_refresher_calls_get_iam_token_with_force_refresh(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        # Use a very short refresh interval for testing
        store = ServiceAccountStore(mock_settings, refresh_interval=0.01)

        # Mock get_iam_token to track calls
        mock_get_iam_token = AsyncMock(return_value="test-token")
        mocker.patch.object(store, "get_iam_token", mock_get_iam_token)

        # Mock random to return 0 for predictable timing
        mocker.patch("mcp_tracker.tracker.custom.client.random.random", return_value=0)

        await store.prepare()

        # Allow the refresher to run at least once
        await asyncio.sleep(0.05)

        await store.close()

        # Verify get_iam_token was called with force_refresh=True
        mock_get_iam_token.assert_called_with(force_refresh=True)
        assert mock_get_iam_token.call_count >= 1

    async def test_refresher_runs_multiple_times(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        # Use a very short refresh interval for testing
        store = ServiceAccountStore(mock_settings, refresh_interval=0.01)

        # Mock get_iam_token to track calls
        call_count = 0

        async def mock_get_iam_token(*, force_refresh: bool = False) -> str:
            nonlocal call_count
            call_count += 1
            return f"token-{call_count}"

        mocker.patch.object(store, "get_iam_token", mock_get_iam_token)
        # Mock random to return 0 for predictable timing
        mocker.patch("mcp_tracker.tracker.custom.client.random.random", return_value=0)

        await store.prepare()

        # Allow the refresher to run multiple times
        await asyncio.sleep(0.05)

        await store.close()

        # Verify get_iam_token was called multiple times
        assert call_count >= 2

    async def test_refresher_continues_after_error(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        store = ServiceAccountStore(
            mock_settings, refresh_interval=0.05, retry_interval=0.01
        )

        call_count = 0

        async def mock_get_iam_token(*, force_refresh: bool = False) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Network error")
            return "token"

        mocker.patch.object(store, "get_iam_token", mock_get_iam_token)
        mocker.patch("mcp_tracker.tracker.custom.client.random.random", return_value=0)

        await store.prepare()

        # Allow time for the refresher to run multiple times
        await asyncio.sleep(0.05)

        # The refresh task should still be running (not crashed)
        assert store._refresh_task is not None
        assert not store._refresh_task.done()

        # The refresher should have continued after errors and called multiple times
        assert call_count >= 3

        await store.close()

    async def test_refresher_uses_retry_interval_on_error(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        # Track sleep calls to verify interval usage
        sleep_intervals: list[float] = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay: float) -> None:
            sleep_intervals.append(delay)
            await original_sleep(0.001)

        mocker.patch("asyncio.sleep", mock_sleep)
        mocker.patch("mcp_tracker.tracker.custom.client.random.random", return_value=0)

        refresh_interval = 1.0
        retry_interval = 0.05
        store = ServiceAccountStore(
            mock_settings,
            refresh_interval=refresh_interval,
            retry_interval=retry_interval,
        )

        call_count = 0

        async def mock_get_iam_token(*, force_refresh: bool = False) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Network error")
            return "token"

        mocker.patch.object(store, "get_iam_token", mock_get_iam_token)

        await store.prepare()

        # Allow the refresher to run a few times
        await original_sleep(0.02)

        await store.close()

        # Verify sleep intervals: first two should be retry_interval (errors),
        # third should be refresh_interval (success)
        assert len(sleep_intervals) >= 2
        # First two calls failed, so retry_interval should be used
        assert sleep_intervals[0] == retry_interval
        assert sleep_intervals[1] == retry_interval
        # Third call succeeded, so refresh_interval should be used
        if len(sleep_intervals) >= 3:
            assert sleep_intervals[2] == refresh_interval

    async def test_refresher_uses_configured_interval(
        self, mock_settings: ServiceAccountSettings, mocker: MockerFixture
    ) -> None:
        mock_sdk_class = mocker.patch(
            "mcp_tracker.tracker.custom.client.yandexcloud.SDK"
        )
        mock_sdk = mocker.Mock()
        mock_sdk.client.return_value = mocker.Mock()
        mock_sdk_class.return_value = mock_sdk

        # Track sleep calls to verify interval usage
        sleep_intervals: list[float] = []
        original_sleep = asyncio.sleep

        async def mock_sleep(delay: float) -> None:
            sleep_intervals.append(delay)
            await original_sleep(0.001)  # Actually sleep briefly

        mocker.patch("asyncio.sleep", mock_sleep)
        mocker.patch("mcp_tracker.tracker.custom.client.random.random", return_value=0)

        custom_interval = 0.05
        store = ServiceAccountStore(mock_settings, refresh_interval=custom_interval)

        mock_get_iam_token = AsyncMock(return_value="test-token")
        mocker.patch.object(store, "get_iam_token", mock_get_iam_token)

        await store.prepare()

        # Allow the refresher to run at least once (use original_sleep to avoid being captured)
        await original_sleep(0.02)

        await store.close()

        # Verify sleep was called with the configured interval (plus jitter)
        assert len(sleep_intervals) >= 1
        # With random.random() mocked to 0, jitter is 0
        assert sleep_intervals[0] == custom_interval
