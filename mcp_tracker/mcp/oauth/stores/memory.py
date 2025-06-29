import time

from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.types import YandexOauthAuthorizationCode, YandexOAuthState


class InMemoryOAuthStore(OAuthStore):
    """In-memory implementation of OAuthStore interface."""

    def __init__(self):
        self._dynamic_clients: dict[str, OAuthClientInformationFull] = {}
        self._states: dict[str, YandexOAuthState] = {}
        self._auth_codes: dict[str, YandexOauthAuthorizationCode] = {}
        self._tokens: dict[str, AccessToken] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}
        self._refresh2access_tokens: dict[str, str] = {}

        # TTL tracking for temporary data
        self._state_expiry: dict[str, float] = {}
        self._auth_code_expiry: dict[str, float] = {}

    async def save_client(self, client: OAuthClientInformationFull) -> None:
        """Save a client to the in-memory store."""
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

        # Save access token
        self._tokens[token.access_token] = AccessToken(
            token=token.access_token,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(time.time() + token.expires_in),
            resource=resource,
        )

        # Save refresh token if provided
        if token.refresh_token is not None:
            self._refresh_tokens[token.refresh_token] = RefreshToken(
                token=token.refresh_token,
                client_id=client_id,
                scopes=scopes,
            )

            # Map refresh token to access token for cleanup
            self._refresh2access_tokens[token.refresh_token] = token.access_token

    async def get_access_token(self, token: str) -> AccessToken | None:
        """Get an access token if it exists and hasn't expired."""
        access_token = self._tokens.get(token)
        if not access_token:
            return None

        # Check if expired
        if access_token.expires_at and access_token.expires_at < time.time():
            del self._tokens[token]
            return None

        return access_token

    async def get_refresh_token(self, token: str) -> RefreshToken | None:
        """Get a refresh token if it exists and hasn't expired."""
        ref_token = self._refresh_tokens.get(token)
        if ref_token is None:
            return None

        # Check if expired (if expiry is set)
        if ref_token.expires_at and ref_token.expires_at < time.time():
            # Token is expired, remove it
            del self._refresh_tokens[token]
            if token in self._refresh2access_tokens:
                del self._refresh2access_tokens[token]
            return None

        return ref_token

    async def revoke_refresh_token(self, token: str) -> None:
        """Delete a refresh token and its associated mappings."""
        if token in self._refresh_tokens:
            # Get associated access token
            access_token_val = self._refresh2access_tokens.get(token)

            # Delete refresh token
            del self._refresh_tokens[token]

            # Delete mapping
            if token in self._refresh2access_tokens:
                del self._refresh2access_tokens[token]

            # Delete associated access token
            if access_token_val and access_token_val in self._tokens:
                del self._tokens[access_token_val]
