import pytest
from mcp.server.auth.provider import RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl
from pytest_mock import MockerFixture

from mcp_tracker.mcp.oauth.stores.memory import InMemoryOAuthStore
from mcp_tracker.mcp.oauth.types import YandexOauthAuthorizationCode, YandexOAuthState


@pytest.fixture
def memory_store() -> InMemoryOAuthStore:
    return InMemoryOAuthStore()


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


class TestInMemoryOAuthStoreClient:
    async def test_save_and_get_client(
        self,
        memory_store: InMemoryOAuthStore,
        sample_client: OAuthClientInformationFull,
    ) -> None:
        await memory_store.save_client(sample_client)
        retrieved_client = await memory_store.get_client("test-client-id")

        assert retrieved_client is not None
        assert retrieved_client == sample_client
        assert retrieved_client.client_id == "test-client-id"
        assert retrieved_client.client_secret == "test-client-secret"

    async def test_get_nonexistent_client(
        self, memory_store: InMemoryOAuthStore
    ) -> None:
        client = await memory_store.get_client("nonexistent-client")
        assert client is None


class TestInMemoryOAuthStoreState:
    async def test_save_and_get_state(
        self, memory_store: InMemoryOAuthStore, sample_oauth_state: YandexOAuthState
    ) -> None:
        state_id = "test-state-id"

        await memory_store.save_state(sample_oauth_state, state_id=state_id)
        retrieved_state = await memory_store.get_state(state_id)

        assert retrieved_state is not None
        assert retrieved_state == sample_oauth_state
        assert retrieved_state.client_id == "test-client-id"

    async def test_get_state_single_use(
        self, memory_store: InMemoryOAuthStore, sample_oauth_state: YandexOAuthState
    ) -> None:
        state_id = "test-state-id"

        await memory_store.save_state(sample_oauth_state, state_id=state_id)

        first_retrieval = await memory_store.get_state(state_id)
        second_retrieval = await memory_store.get_state(state_id)

        assert first_retrieval == sample_oauth_state
        assert second_retrieval is None

    async def test_save_state_with_ttl(
        self,
        memory_store: InMemoryOAuthStore,
        sample_oauth_state: YandexOAuthState,
        mocker: MockerFixture,
    ) -> None:
        state_id = "test-state-id"
        ttl = 1

        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1000.0
        await memory_store.save_state(sample_oauth_state, state_id=state_id, ttl=ttl)

        # Time hasn't passed, state should be available
        retrieved_state = await memory_store.get_state(state_id)
        assert retrieved_state == sample_oauth_state

    async def test_state_expiry(
        self,
        memory_store: InMemoryOAuthStore,
        sample_oauth_state: YandexOAuthState,
        mocker: MockerFixture,
    ) -> None:
        state_id = "test-state-id"
        ttl = 1

        mock_time = mocker.patch("time.time")
        # Set initial time
        mock_time.return_value = 1000.0
        await memory_store.save_state(sample_oauth_state, state_id=state_id, ttl=ttl)

        # Move time forward beyond TTL
        mock_time.return_value = 1002.0
        retrieved_state = await memory_store.get_state(state_id)

        assert retrieved_state is None

    async def test_get_nonexistent_state(
        self, memory_store: InMemoryOAuthStore
    ) -> None:
        state = await memory_store.get_state("nonexistent-state")
        assert state is None


class TestInMemoryOAuthStoreAuthCode:
    async def test_save_and_get_auth_code(
        self,
        memory_store: InMemoryOAuthStore,
        sample_auth_code: YandexOauthAuthorizationCode,
    ) -> None:
        await memory_store.save_auth_code(sample_auth_code)
        retrieved_code = await memory_store.get_auth_code("test-auth-code")

        assert retrieved_code is not None
        assert retrieved_code == sample_auth_code
        assert retrieved_code.yandex_auth_code == "yandex-code-123"

    async def test_get_auth_code_single_use(
        self,
        memory_store: InMemoryOAuthStore,
        sample_auth_code: YandexOauthAuthorizationCode,
    ) -> None:
        await memory_store.save_auth_code(sample_auth_code)

        first_retrieval = await memory_store.get_auth_code("test-auth-code")
        second_retrieval = await memory_store.get_auth_code("test-auth-code")

        assert first_retrieval == sample_auth_code
        assert second_retrieval is None

    async def test_save_auth_code_with_ttl(
        self,
        memory_store: InMemoryOAuthStore,
        sample_auth_code: YandexOauthAuthorizationCode,
        mocker: MockerFixture,
    ) -> None:
        ttl = 1

        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1000.0
        await memory_store.save_auth_code(sample_auth_code, ttl=ttl)

        retrieved_code = await memory_store.get_auth_code("test-auth-code")
        assert retrieved_code == sample_auth_code

    async def test_auth_code_expiry(
        self,
        memory_store: InMemoryOAuthStore,
        sample_auth_code: YandexOauthAuthorizationCode,
        mocker: MockerFixture,
    ) -> None:
        ttl = 1

        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1000.0
        await memory_store.save_auth_code(sample_auth_code, ttl=ttl)

        mock_time.return_value = 1002.0
        retrieved_code = await memory_store.get_auth_code("test-auth-code")

        assert retrieved_code is None

    async def test_get_nonexistent_auth_code(
        self, memory_store: InMemoryOAuthStore
    ) -> None:
        code = await memory_store.get_auth_code("nonexistent-code")
        assert code is None


class TestInMemoryOAuthStoreTokens:
    async def test_save_and_get_oauth_token(
        self,
        memory_store: InMemoryOAuthStore,
        sample_oauth_token: OAuthToken,
        mocker: MockerFixture,
    ) -> None:
        client_id = "test-client-id"
        scopes = ["read", "write"]
        resource = "test-resource"

        mocker.patch("time.time", return_value=1000.0)
        await memory_store.save_oauth_token(
            sample_oauth_token, client_id, scopes, resource
        )

        access_token = await memory_store.get_access_token("test-access-token")
        refresh_token = await memory_store.get_refresh_token("test-refresh-token")

        assert access_token is not None
        assert access_token.token == "test-access-token"
        assert access_token.client_id == client_id
        assert access_token.scopes == scopes
        assert access_token.resource == resource
        assert access_token.expires_at == 1000 + 3600

        assert refresh_token is not None
        assert refresh_token.token == "test-refresh-token"
        assert refresh_token.client_id == client_id
        assert refresh_token.scopes == scopes

    async def test_save_oauth_token_without_refresh(
        self, memory_store: InMemoryOAuthStore, mocker: MockerFixture
    ) -> None:
        oauth_token = OAuthToken(
            access_token="test-access-token",
            token_type="Bearer",
            expires_in=3600,
            scope="read",
        )

        mocker.patch("time.time", return_value=1000.0)
        await memory_store.save_oauth_token(oauth_token, "client-id", ["read"], None)

        access_token = await memory_store.get_access_token("test-access-token")
        refresh_token = await memory_store.get_refresh_token("nonexistent-refresh")

        assert access_token is not None
        assert refresh_token is None

    async def test_oauth_token_assertion_error(
        self, memory_store: InMemoryOAuthStore
    ) -> None:
        oauth_token = OAuthToken(
            access_token="test-access-token",
            token_type="Bearer",
            scope="read",
        )

        with pytest.raises(AssertionError, match="expires_in must be provided"):
            await memory_store.save_oauth_token(
                oauth_token, "client-id", ["read"], None
            )

    async def test_access_token_expiry(
        self,
        memory_store: InMemoryOAuthStore,
        sample_oauth_token: OAuthToken,
        mocker: MockerFixture,
    ) -> None:
        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1000.0
        await memory_store.save_oauth_token(
            sample_oauth_token, "client-id", ["read"], None
        )

        # Token should be valid
        mock_time.return_value = 1500.0
        access_token = await memory_store.get_access_token("test-access-token")
        assert access_token is not None

        # Token should be expired
        mock_time.return_value = 5000.0
        access_token = await memory_store.get_access_token("test-access-token")
        assert access_token is None

    async def test_refresh_token_expiry(
        self, memory_store: InMemoryOAuthStore, mocker: MockerFixture
    ) -> None:
        refresh_token = RefreshToken(
            token="test-refresh-token",
            client_id="client-id",
            scopes=["read"],
            expires_at=1500,
        )

        memory_store._refresh_tokens["test-refresh-token"] = refresh_token

        mock_time = mocker.patch("time.time")
        # Token should be valid
        mock_time.return_value = 1400.0
        token = await memory_store.get_refresh_token("test-refresh-token")
        assert token is not None

        # Token should be expired
        mock_time.return_value = 1600.0
        token = await memory_store.get_refresh_token("test-refresh-token")
        assert token is None

    async def test_revoke_refresh_token(
        self,
        memory_store: InMemoryOAuthStore,
        sample_oauth_token: OAuthToken,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch("time.time", return_value=1000.0)
        await memory_store.save_oauth_token(
            sample_oauth_token, "client-id", ["read"], None
        )

        # Verify tokens exist
        access_token = await memory_store.get_access_token("test-access-token")
        refresh_token = await memory_store.get_refresh_token("test-refresh-token")
        assert access_token is not None
        assert refresh_token is not None

        # Revoke refresh token
        await memory_store.revoke_refresh_token("test-refresh-token")

        # Verify both tokens are removed
        access_token = await memory_store.get_access_token("test-access-token")
        refresh_token = await memory_store.get_refresh_token("test-refresh-token")
        assert access_token is None
        assert refresh_token is None

    async def test_revoke_nonexistent_refresh_token(
        self, memory_store: InMemoryOAuthStore
    ) -> None:
        await memory_store.revoke_refresh_token("nonexistent-token")

    async def test_get_nonexistent_tokens(
        self, memory_store: InMemoryOAuthStore
    ) -> None:
        access_token = await memory_store.get_access_token("nonexistent-access")
        refresh_token = await memory_store.get_refresh_token("nonexistent-refresh")

        assert access_token is None
        assert refresh_token is None


class TestInMemoryOAuthStoreEdgeCases:
    async def test_state_cleanup_on_expiry(
        self,
        memory_store: InMemoryOAuthStore,
        sample_oauth_state: YandexOAuthState,
        mocker: MockerFixture,
    ) -> None:
        state_id = "test-state-id"

        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1000.0
        await memory_store.save_state(sample_oauth_state, state_id=state_id, ttl=1)

        # Verify state is stored
        assert state_id in memory_store._states
        assert state_id in memory_store._state_expiry

        # Move time forward
        mock_time.return_value = 1002.0
        await memory_store.get_state(state_id)

        # Verify cleanup happened
        assert state_id not in memory_store._states
        assert state_id not in memory_store._state_expiry

    async def test_auth_code_cleanup_on_expiry(
        self,
        memory_store: InMemoryOAuthStore,
        sample_auth_code: YandexOauthAuthorizationCode,
        mocker: MockerFixture,
    ) -> None:
        code_id = "test-auth-code"

        mock_time = mocker.patch("time.time")
        mock_time.return_value = 1000.0
        await memory_store.save_auth_code(sample_auth_code, ttl=1)

        # Verify auth code is stored
        assert code_id in memory_store._auth_codes
        assert code_id in memory_store._auth_code_expiry

        # Move time forward
        mock_time.return_value = 1002.0
        await memory_store.get_auth_code(code_id)

        # Verify cleanup happened
        assert code_id not in memory_store._auth_codes
        assert code_id not in memory_store._auth_code_expiry

    async def test_state_without_ttl(
        self, memory_store: InMemoryOAuthStore, sample_oauth_state: YandexOAuthState
    ) -> None:
        state_id = "test-state-id"

        await memory_store.save_state(sample_oauth_state, state_id=state_id)

        # Should not have expiry tracking
        assert state_id not in memory_store._state_expiry

        # Should still be retrievable
        retrieved_state = await memory_store.get_state(state_id)
        assert retrieved_state == sample_oauth_state

    async def test_auth_code_without_ttl(
        self,
        memory_store: InMemoryOAuthStore,
        sample_auth_code: YandexOauthAuthorizationCode,
    ) -> None:
        await memory_store.save_auth_code(sample_auth_code)

        # Should not have expiry tracking
        assert "test-auth-code" not in memory_store._auth_code_expiry

        # Should still be retrievable
        retrieved_code = await memory_store.get_auth_code("test-auth-code")
        assert retrieved_code == sample_auth_code
