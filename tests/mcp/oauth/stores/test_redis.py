from typing import Any

import pytest
from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl
from pytest_mock import MockerFixture

from mcp_tracker.mcp.oauth.stores.redis import RedisOAuthStore
from mcp_tracker.mcp.oauth.stores.serializers import PydanticJsonSerializer
from mcp_tracker.mcp.oauth.types import YandexOauthAuthorizationCode, YandexOAuthState


@pytest.fixture
def mock_cache(mocker: MockerFixture) -> Any:
    cache = mocker.AsyncMock()
    cache.get = mocker.AsyncMock()
    cache.set = mocker.AsyncMock()
    cache.delete = mocker.AsyncMock()
    return cache


@pytest.fixture
def redis_store(mock_cache: Any, mocker: MockerFixture) -> RedisOAuthStore:
    mock_cache_class = mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")
    mock_cache_class.return_value = mock_cache
    return RedisOAuthStore(
        endpoint="localhost",
        port=6379,
        db=0,
        password="test-password",
        pool_max_size=5,
    )


@pytest.fixture
def sample_client() -> OAuthClientInformationFull:
    return OAuthClientInformationFull(
        client_id="test-client-id",
        client_secret="test-client-secret",
        client_id_issued_at=None,
        client_secret_expires_at=None,
        redirect_uris=[AnyHttpUrl("https://example.com/callback")],
    )


@pytest.fixture
def sample_oauth_state() -> YandexOAuthState:
    return YandexOAuthState(
        redirect_uri=AnyHttpUrl("https://example.com/callback"),
        code_challenge="test-challenge",
        scopes=["read", "write"],
        redirect_uri_provided_explicitly=True,
        client_id="test-client-id",
        resource="test-resource",
    )


@pytest.fixture
def sample_auth_code() -> YandexOauthAuthorizationCode:
    return YandexOauthAuthorizationCode(
        code="test-auth-code",
        client_id="test-client-id",
        redirect_uri=AnyHttpUrl("https://example.com/callback"),
        scopes=["read", "write"],
        expires_at=2000.0,
        code_challenge="test-challenge",
        redirect_uri_provided_explicitly=True,
        resource=None,
        yandex_auth_code="yandex-code-123",
    )


@pytest.fixture
def sample_oauth_token() -> OAuthToken:
    return OAuthToken(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        token_type="Bearer",
        expires_in=3600,
        scope="read write",
    )


class TestRedisOAuthStoreInit:
    def test_init_with_default_parameters(self, mocker: MockerFixture) -> None:
        mock_cache_class = mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")
        mock_cache = mocker.Mock()
        mock_cache_class.return_value = mock_cache

        RedisOAuthStore()

        mock_cache_class.assert_called_once()
        call_args = mock_cache_class.call_args

        # Check Cache enum is passed as first argument
        assert call_args[0][0] == mock_cache_class.REDIS

        # Check keyword arguments
        kwargs = call_args[1]
        assert kwargs["endpoint"] == "localhost"
        assert kwargs["port"] == 6379
        assert kwargs["db"] == 0
        assert kwargs["password"] is None
        assert kwargs["pool_max_size"] == 10
        assert "serializer" in kwargs

    def test_init_with_custom_parameters(self, mocker: MockerFixture) -> None:
        mock_cache_class = mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")
        mock_cache = mocker.Mock()
        mock_cache_class.return_value = mock_cache

        RedisOAuthStore(
            endpoint="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            pool_max_size=20,
            custom_param="custom_value",
        )

        call_args = mock_cache_class.call_args
        kwargs = call_args[1]
        assert kwargs["endpoint"] == "redis.example.com"
        assert kwargs["port"] == 6380
        assert kwargs["db"] == 1
        assert kwargs["password"] == "secret"
        assert kwargs["pool_max_size"] == 20
        assert kwargs["custom_param"] == "custom_value"

    def test_key_methods(self, mocker: MockerFixture) -> None:
        mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")
        store = RedisOAuthStore()

        assert store._client_key("client123") == "oauth:client:client123"
        assert store._state_key("state456") == "oauth:state:state456"
        assert store._auth_code_key("code789") == "oauth:authcode:code789"
        assert store._access_token_key("token123") == "oauth:access:token123"
        assert store._refresh_token_key("refresh456") == "oauth:refresh:refresh456"
        assert store._mapping_key("refresh789") == "oauth:mapping:refresh789"


class TestRedisOAuthStoreClient:
    async def test_save_client(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_client: OAuthClientInformationFull,
    ) -> None:
        await redis_store.save_client(sample_client)

        mock_cache.set.assert_called_once_with(
            "oauth:client:test-client-id", sample_client
        )

    async def test_get_client_success(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_client: OAuthClientInformationFull,
    ) -> None:
        mock_cache.get.return_value = sample_client.model_dump()

        result = await redis_store.get_client("test-client-id")

        mock_cache.get.assert_called_once_with("oauth:client:test-client-id")
        assert result == sample_client

    async def test_get_client_not_found(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = None

        result = await redis_store.get_client("nonexistent-client")

        assert result is None


class TestRedisOAuthStoreState:
    async def test_save_state_with_ttl(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_oauth_state: YandexOAuthState,
    ) -> None:
        await redis_store.save_state(sample_oauth_state, state_id="state123", ttl=300)

        mock_cache.set.assert_called_once_with(
            "oauth:state:state123", sample_oauth_state, ttl=300
        )

    async def test_save_state_without_ttl(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_oauth_state: YandexOAuthState,
    ) -> None:
        await redis_store.save_state(sample_oauth_state, state_id="state123")

        mock_cache.set.assert_called_once_with(
            "oauth:state:state123", sample_oauth_state, ttl=None
        )

    async def test_get_state_success(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_oauth_state: YandexOAuthState,
    ) -> None:
        mock_cache.get.return_value = sample_oauth_state.model_dump()

        result = await redis_store.get_state("state123")

        # Should get and then delete (single-use)
        mock_cache.get.assert_called_once_with("oauth:state:state123")
        mock_cache.delete.assert_called_once_with("oauth:state:state123")
        assert result == sample_oauth_state

    async def test_get_state_not_found(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = None

        result = await redis_store.get_state("nonexistent-state")

        mock_cache.get.assert_called_once_with("oauth:state:nonexistent-state")
        mock_cache.delete.assert_not_called()
        assert result is None


class TestRedisOAuthStoreAuthCode:
    async def test_save_auth_code_with_ttl(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_auth_code: YandexOauthAuthorizationCode,
    ) -> None:
        await redis_store.save_auth_code(sample_auth_code, ttl=600)

        mock_cache.set.assert_called_once_with(
            "oauth:authcode:test-auth-code", sample_auth_code, ttl=600
        )

    async def test_save_auth_code_without_ttl(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_auth_code: YandexOauthAuthorizationCode,
    ) -> None:
        await redis_store.save_auth_code(sample_auth_code)

        mock_cache.set.assert_called_once_with(
            "oauth:authcode:test-auth-code", sample_auth_code, ttl=None
        )

    async def test_get_auth_code_success(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_auth_code: YandexOauthAuthorizationCode,
    ) -> None:
        mock_cache.get.return_value = sample_auth_code.model_dump()

        result = await redis_store.get_auth_code("test-auth-code")

        # Should get and then delete (single-use)
        mock_cache.get.assert_called_once_with("oauth:authcode:test-auth-code")
        mock_cache.delete.assert_called_once_with("oauth:authcode:test-auth-code")
        assert result == sample_auth_code

    async def test_get_auth_code_not_found(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = None

        result = await redis_store.get_auth_code("nonexistent-code")

        mock_cache.get.assert_called_once_with("oauth:authcode:nonexistent-code")
        mock_cache.delete.assert_not_called()
        assert result is None


class TestRedisOAuthStoreTokens:
    async def test_save_oauth_token_with_refresh(
        self,
        redis_store: RedisOAuthStore,
        mock_cache: Any,
        sample_oauth_token: OAuthToken,
        mocker: MockerFixture,
    ) -> None:
        client_id = "test-client-id"
        scopes = ["read", "write"]
        resource = "test-resource"

        mocker.patch("time.time", return_value=1000.0)
        await redis_store.save_oauth_token(
            sample_oauth_token, client_id, scopes, resource
        )

        assert mock_cache.set.call_count == 3

        # Check access token call
        access_token_call = mock_cache.set.call_args_list[0]
        assert access_token_call[0][0] == "oauth:access:test-access-token"
        access_token_data = access_token_call[0][1]
        assert access_token_data.token == "test-access-token"
        assert access_token_data.client_id == client_id
        assert access_token_data.scopes == scopes
        assert access_token_data.resource == resource
        assert access_token_data.expires_at == 1000 + 3600
        assert access_token_call[1]["ttl"] == 3600

        # Check refresh token call
        refresh_token_call = mock_cache.set.call_args_list[1]
        assert refresh_token_call[0][0] == "oauth:refresh:test-refresh-token"
        refresh_token_data = refresh_token_call[0][1]
        assert refresh_token_data.token == "test-refresh-token"
        assert refresh_token_data.client_id == client_id
        assert refresh_token_data.scopes == scopes
        assert refresh_token_call[1]["ttl"] == 31 * 24 * 60 * 60

        # Check mapping call
        mapping_call = mock_cache.set.call_args_list[2]
        assert mapping_call[0][0] == "oauth:mapping:test-refresh-token"
        assert mapping_call[0][1] == "test-access-token"

    async def test_save_oauth_token_without_refresh(
        self, redis_store: RedisOAuthStore, mock_cache: Any, mocker: MockerFixture
    ) -> None:
        oauth_token = OAuthToken(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=3600,
            scope="read",
        )

        mocker.patch("time.time", return_value=1000.0)
        await redis_store.save_oauth_token(oauth_token, "client-id", ["read"], None)

        # Should only call set once (for access token)
        assert mock_cache.set.call_count == 1
        access_token_call = mock_cache.set.call_args_list[0]
        assert access_token_call[0][0] == "oauth:access:test-access-token"

    async def test_save_oauth_token_assertion_error(
        self, redis_store: RedisOAuthStore
    ) -> None:
        oauth_token = OAuthToken(
            access_token="test-access-token",
            token_type="Bearer",
            scope="read",
        )

        with pytest.raises(AssertionError, match="expires_in must be provided"):
            await redis_store.save_oauth_token(oauth_token, "client-id", ["read"], None)

    async def test_get_access_token_success(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        access_token_data = AccessToken(
            token="test-access-token",
            client_id="client-id",
            scopes=["read"],
            expires_at=2000,
        )
        mock_cache.get.return_value = access_token_data.model_dump()

        result = await redis_store.get_access_token("test-access-token")

        mock_cache.get.assert_called_once_with("oauth:access:test-access-token")
        assert result == access_token_data

    async def test_get_access_token_not_found(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = None

        result = await redis_store.get_access_token("nonexistent-token")

        assert result is None

    async def test_get_refresh_token_success(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        refresh_token_data = RefreshToken(
            token="test-refresh-token",
            client_id="client-id",
            scopes=["read"],
        )
        mock_cache.get.return_value = refresh_token_data.model_dump()

        result = await redis_store.get_refresh_token("test-refresh-token")

        mock_cache.get.assert_called_once_with("oauth:refresh:test-refresh-token")
        assert result == refresh_token_data

    async def test_get_refresh_token_not_found(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = None

        result = await redis_store.get_refresh_token("nonexistent-token")

        assert result is None

    async def test_revoke_refresh_token_with_access_token(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = "test-access-token"

        await redis_store.revoke_refresh_token("test-refresh-token")

        # Should get the mapping first
        mock_cache.get.assert_called_once_with("oauth:mapping:test-refresh-token")

        # Should delete refresh token, mapping, and access token
        assert mock_cache.delete.call_count == 3
        delete_calls = [call[0][0] for call in mock_cache.delete.call_args_list]
        assert "oauth:refresh:test-refresh-token" in delete_calls
        assert "oauth:mapping:test-refresh-token" in delete_calls
        assert "oauth:access:test-access-token" in delete_calls

    async def test_revoke_refresh_token_without_access_token(
        self, redis_store: RedisOAuthStore, mock_cache: Any
    ) -> None:
        mock_cache.get.return_value = None

        await redis_store.revoke_refresh_token("test-refresh-token")

        # Should still delete refresh token and mapping
        assert mock_cache.delete.call_count == 2
        delete_calls = [call[0][0] for call in mock_cache.delete.call_args_list]
        assert "oauth:refresh:test-refresh-token" in delete_calls
        assert "oauth:mapping:test-refresh-token" in delete_calls


class TestRedisOAuthStoreEdgeCases:
    async def test_refresh_token_ttl_constant(self, mocker: MockerFixture) -> None:
        mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")
        store = RedisOAuthStore()

        # Should be 31 days in seconds
        expected_ttl = 31 * 24 * 60 * 60
        assert store._refresh_token_ttl == expected_ttl

    async def test_key_prefixes(self, mocker: MockerFixture) -> None:
        mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")
        store = RedisOAuthStore()

        assert store._CLIENT_KEY_PREFIX == "oauth:client:"
        assert store._STATE_KEY_PREFIX == "oauth:state:"
        assert store._AUTH_CODE_KEY_PREFIX == "oauth:authcode:"
        assert store._ACCESS_TOKEN_KEY_PREFIX == "oauth:access:"
        assert store._REFRESH_TOKEN_KEY_PREFIX == "oauth:refresh:"
        assert store._MAPPING_KEY_PREFIX == "oauth:mapping:"

    async def test_serializer_configuration(self, mocker: MockerFixture) -> None:
        mock_cache_class = mocker.patch("mcp_tracker.mcp.oauth.stores.redis.Cache")

        RedisOAuthStore()

        # Should create serializer and pass it to Cache
        call_args = mock_cache_class.call_args[1]
        assert isinstance(call_args["serializer"], PydanticJsonSerializer)
