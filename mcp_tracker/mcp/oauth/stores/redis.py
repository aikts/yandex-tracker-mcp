import time
from typing import Any

from aiocache import Cache
from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from mcp_tracker.mcp.oauth.serializers import PydanticJsonSerializer
from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.types import YandexOauthAuthorizationCode, YandexOAuthState


class RedisOAuthStore(OAuthStore):
    """Redis-based implementation of OAuthStore interface."""

    # Redis key prefixes
    _CLIENT_KEY_PREFIX = "oauth:client:"
    _STATE_KEY_PREFIX = "oauth:state:"
    _AUTH_CODE_KEY_PREFIX = "oauth:authcode:"
    _ACCESS_TOKEN_KEY_PREFIX = "oauth:access:"
    _REFRESH_TOKEN_KEY_PREFIX = "oauth:refresh:"
    _MAPPING_KEY_PREFIX = "oauth:mapping:"

    def __init__(
        self,
        endpoint: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        pool_max_size: int = 10,
        **kwargs: Any,
    ):
        self._cache = Cache(
            Cache.REDIS,
            endpoint=endpoint,
            port=port,
            db=db,
            password=password,
            serializer=PydanticJsonSerializer(),
            pool_max_size=pool_max_size,
            **kwargs,
        )
        self._refresh_token_ttl = (
            31 * 24 * 60 * 60
        )  # 31 days - https://yandex.cloud/en-ru/docs/iam/concepts/authorization/refresh-token#token-lifetime

    def _client_key(self, client_id: str) -> str:
        """Build Redis key for client storage."""
        return f"{self._CLIENT_KEY_PREFIX}{client_id}"

    def _state_key(self, state_id: str) -> str:
        """Build Redis key for OAuth state storage."""
        return f"{self._STATE_KEY_PREFIX}{state_id}"

    def _auth_code_key(self, code_id: str) -> str:
        """Build Redis key for authorization code storage."""
        return f"{self._AUTH_CODE_KEY_PREFIX}{code_id}"

    def _access_token_key(self, token: str) -> str:
        """Build Redis key for access token storage."""
        return f"{self._ACCESS_TOKEN_KEY_PREFIX}{token}"

    def _refresh_token_key(self, token: str) -> str:
        """Build Redis key for refresh token storage."""
        return f"{self._REFRESH_TOKEN_KEY_PREFIX}{token}"

    def _mapping_key(self, refresh_token: str) -> str:
        """Build Redis key for refresh-to-access token mapping."""
        return f"{self._MAPPING_KEY_PREFIX}{refresh_token}"

    async def save_client(self, client: OAuthClientInformationFull) -> None:
        """Save a client to Redis."""
        await self._cache.set(self._client_key(client.client_id), client)

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Retrieve a client from Redis."""
        data = await self._cache.get(self._client_key(client_id))
        if data is None:
            return None
        return OAuthClientInformationFull.model_validate(data)

    async def save_state(
        self, state: YandexOAuthState, *, state_id: str, ttl: int | None = None
    ) -> None:
        """Save an OAuth state with optional TTL."""
        await self._cache.set(self._state_key(state_id), state, ttl=ttl)

    async def get_state(self, state_id: str) -> YandexOAuthState | None:
        """Get and remove an OAuth state if it exists."""
        key = self._state_key(state_id)
        data = await self._cache.get(key)
        if data is not None:
            # States are single-use, so delete after retrieval
            await self._cache.delete(key)
            return YandexOAuthState.model_validate(data)
        return None

    async def save_auth_code(
        self, code: YandexOauthAuthorizationCode, *, ttl: int | None = None
    ) -> None:
        """Save an authorization code with optional TTL."""
        await self._cache.set(self._auth_code_key(code.code), code, ttl=ttl)

    async def get_auth_code(self, code_id: str) -> YandexOauthAuthorizationCode | None:
        """Get and remove an authorization code if it exists."""
        key = self._auth_code_key(code_id)
        data = await self._cache.get(key)
        if data is not None:
            # Auth codes are single-use, so delete after retrieval
            await self._cache.delete(key)
            return YandexOauthAuthorizationCode.model_validate(data)
        return None

    async def save_oauth_token(
        self, token: OAuthToken, client_id: str, scopes: list[str], resource: str | None
    ) -> None:
        """Save an OAuth token and its metadata."""
        assert token.expires_in is not None, "expires_in must be provided"

        current_time = int(time.time())
        expires_at = current_time + token.expires_in

        # Save access token
        access_token = AccessToken(
            token=token.access_token,
            client_id=client_id,
            scopes=scopes,
            expires_at=expires_at,
            resource=resource,
        )
        await self._cache.set(
            self._access_token_key(token.access_token),
            access_token,
            ttl=token.expires_in,
        )

        # Save refresh token if provided
        if token.refresh_token is not None:
            refresh_token = RefreshToken(
                token=token.refresh_token,
                client_id=client_id,
                scopes=scopes,
                expires_at=current_time + self._refresh_token_ttl,
            )
            await self._cache.set(
                self._refresh_token_key(token.refresh_token),
                refresh_token,
                ttl=self._refresh_token_ttl,
            )

            # Map refresh token to access token for cleanup
            await self._cache.set(
                self._mapping_key(token.refresh_token), token.access_token
            )

    async def get_access_token(self, token: str) -> AccessToken | None:
        """Get an access token if it exists and hasn't expired."""
        data = await self._cache.get(self._access_token_key(token))
        if data is None:
            return None
        return AccessToken.model_validate(data)

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        """Get a refresh token if it exists."""
        data = await self._cache.get(self._refresh_token_key(token))
        if data is None:
            return None

        return RefreshToken.model_validate(data)

    async def revoke_refresh_token(self, token: str) -> None:
        """Delete a refresh token and its associated mappings."""
        # Get associated access token
        access_token_val = await self._cache.get(self._mapping_key(token))

        # Delete refresh token
        await self._cache.delete(self._refresh_token_key(token))

        # Delete mapping
        await self._cache.delete(self._mapping_key(token))

        # Delete associated access token
        if access_token_val:
            await self._cache.delete(self._access_token_key(access_token_val))
