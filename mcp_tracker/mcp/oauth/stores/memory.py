import time

from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.types import YandexOauthAuthorizationCode, YandexOAuthState

from .crypto import hash_token


class InMemoryOAuthStore(OAuthStore):
    """In-memory implementation of OAuthStore interface.

    Uses hashed tokens as dictionary keys for consistency with RedisOAuthStore,
    providing some protection against accidental token exposure in logs/dumps.
    """

    def __init__(self) -> None:
        self._dynamic_clients: dict[str, OAuthClientInformationFull] = {}
        self._states: dict[str, YandexOAuthState] = {}
        self._auth_codes: dict[str, YandexOauthAuthorizationCode] = {}
        # Keys are hashed tokens, values contain the original token
        self._tokens: dict[str, AccessToken] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}
        # Maps hashed refresh token -> hashed access token
        self._refresh2access_tokens: dict[str, str] = {}

        # TTL tracking for temporary data
        self._state_expiry: dict[str, float] = {}
        self._auth_code_expiry: dict[str, float] = {}

    async def save_client(self, client: OAuthClientInformationFull) -> None:
        """Save a client to the in-memory store."""
        assert client.client_id is not None, "client_id must be provided"
        self._dynamic_clients[client.client_id] = client

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Retrieve a client from the in-memory store."""
        return self._dynamic_clients.get(client_id)

    async def save_state(
        self, state: YandexOAuthState, *, state_id: str, ttl: int | None = None
    ) -> None:
        """Save an OAuth state with optional TTL."""
        self._states[state_id] = state
        if ttl is not None:
            self._state_expiry[state_id] = time.time() + ttl

    async def get_state(self, state_id: str) -> YandexOAuthState | None:
        """Get and remove an OAuth state if it exists and hasn't expired."""
        # Check expiry
        if state_id in self._state_expiry:
            if time.time() > self._state_expiry[state_id]:
                # Expired - clean up
                del self._states[state_id]
                del self._state_expiry[state_id]
                return None

        # Return and remove state (states are single-use)
        state = self._states.get(state_id)
        if state is not None:
            del self._states[state_id]
            if state_id in self._state_expiry:
                del self._state_expiry[state_id]
        return state

    async def save_auth_code(
        self, code: YandexOauthAuthorizationCode, *, ttl: int | None = None
    ) -> None:
        """Save an authorization code with optional TTL."""
        self._auth_codes[code.code] = code
        if ttl is not None:
            self._auth_code_expiry[code.code] = time.time() + ttl

    async def get_auth_code(self, code_id: str) -> YandexOauthAuthorizationCode | None:
        """Get and remove an authorization code if it exists and hasn't expired."""
        # Check expiry
        if code_id in self._auth_code_expiry:
            if time.time() > self._auth_code_expiry[code_id]:
                # Expired - clean up
                del self._auth_codes[code_id]
                del self._auth_code_expiry[code_id]
                return None

        # Return and remove auth code (auth codes are single-use)
        auth_code = self._auth_codes.get(code_id)
        if auth_code is not None:
            del self._auth_codes[code_id]
            if code_id in self._auth_code_expiry:
                del self._auth_code_expiry[code_id]
        return auth_code

    async def save_oauth_token(
        self, token: OAuthToken, client_id: str, scopes: list[str], resource: str | None
    ) -> None:
        """Save an OAuth token and its metadata."""
        assert token.expires_in is not None, "expires_in must be provided"

        access_token_hash = hash_token(token.access_token)

        # Save access token (keyed by hash)
        self._tokens[access_token_hash] = AccessToken(
            token=token.access_token,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(time.time() + token.expires_in),
            resource=resource,
        )

        # Save refresh token if provided
        if token.refresh_token is not None:
            refresh_token_hash = hash_token(token.refresh_token)

            self._refresh_tokens[refresh_token_hash] = RefreshToken(
                token=token.refresh_token,
                client_id=client_id,
                scopes=scopes,
            )

            # Map refresh token hash to access token hash for cleanup
            self._refresh2access_tokens[refresh_token_hash] = access_token_hash

    async def get_access_token(self, token: str) -> AccessToken | None:
        """Get an access token if it exists and hasn't expired."""
        token_hash = hash_token(token)
        access_token = self._tokens.get(token_hash)
        if not access_token:
            return None

        # Check if expired
        if access_token.expires_at and access_token.expires_at < time.time():
            del self._tokens[token_hash]
            return None

        return access_token

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        """Get a refresh token if it exists and hasn't expired."""
        token_hash = hash_token(token)
        ref_token = self._refresh_tokens.get(token_hash)
        if ref_token is None:
            return None

        # Check if expired (if expiry is set)
        if ref_token.expires_at and ref_token.expires_at < time.time():
            # Token is expired, remove it
            del self._refresh_tokens[token_hash]
            if token_hash in self._refresh2access_tokens:
                del self._refresh2access_tokens[token_hash]
            return None

        return ref_token

    async def revoke_refresh_token(self, token: str) -> None:
        """Delete a refresh token and its associated mappings."""
        token_hash = hash_token(token)
        if token_hash in self._refresh_tokens:
            # Get associated access token hash
            access_token_hash = self._refresh2access_tokens.get(token_hash)

            # Delete refresh token
            del self._refresh_tokens[token_hash]

            # Delete mapping
            if token_hash in self._refresh2access_tokens:
                del self._refresh2access_tokens[token_hash]

            # Delete associated access token
            if access_token_hash and access_token_hash in self._tokens:
                del self._tokens[access_token_hash]
