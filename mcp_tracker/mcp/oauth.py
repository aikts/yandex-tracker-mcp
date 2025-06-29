import secrets
import time

import aiohttp
import yarl
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyUrl, BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response


class YandexOAuthState(BaseModel):
    redirect_uri: AnyUrl
    code_challenge: str
    redirect_uri_provided_explicitly: bool
    client_id: str
    resource: str | None = None  # RFC 8707 resource indicator


class YandexCallbackRequest(BaseModel):
    code: str
    state: str
    cid: str | None = None


class YandexOauthAuthorizationCode(AuthorizationCode):
    yandex_auth_code: str


class YandexOAuthAuthorizationServerProvider(
    OAuthAuthorizationServerProvider[
        YandexOauthAuthorizationCode, RefreshToken, AccessToken
    ]
):
    def __init__(self, *, client_id: str, client_secret: str, server_url: yarl.URL):
        self._client_id = client_id
        self._client_secret = client_secret
        self._server_url = server_url
        self._dynamic_clients: dict[str, OAuthClientInformationFull] = {}
        self._states: dict[str, YandexOAuthState] = {}
        self._auth_codes: dict[str, YandexOauthAuthorizationCode] = {}
        self._tokens: dict[str, AccessToken] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}
        self._refresh2access_tokens: dict[str, str] = {}

    async def handle_yandex_callback(self, request: Request) -> Response:
        try:
            # Parse request body as JSON
            params = request.query_params
            yandex_cb_data = YandexCallbackRequest.model_validate(params)

            # Scope validation is handled below
        except ValidationError:
            return JSONResponse(
                content="invalid callback data",
                status_code=400,
            )

        state = self._states[yandex_cb_data.state]
        del self._states[yandex_cb_data.state]

        # Create MCP authorization code
        new_code = f"mcp_{secrets.token_hex(16)}"
        auth_code = YandexOauthAuthorizationCode(
            code=new_code,
            yandex_auth_code=yandex_cb_data.code,
            client_id=state.client_id,
            redirect_uri=state.redirect_uri,
            redirect_uri_provided_explicitly=state.redirect_uri_provided_explicitly,
            expires_at=time.time() + 300,
            scopes=["tracker:write", "tracker:read"],
            code_challenge=state.code_challenge,
            resource=state.resource,  # RFC 8707
        )
        self._auth_codes[new_code] = auth_code

        return RedirectResponse(
            url=construct_redirect_uri(
                str(state.redirect_uri),
                code=new_code,
                state=yandex_cb_data.state,
            ),
            status_code=302,
            headers={"Cache-Control": "no-store"},
        )

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """
        Retrieves client information by client ID.

        Implementors MAY raise NotImplementedError if dynamic client registration is
        disabled in ClientRegistrationOptions.

        Args:
            client_id: The ID of the client to retrieve.

        Returns:
            The client information, or None if the client does not exist.
        """
        return self._dynamic_clients[client_id]

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """
        Saves client information as part of registering it.

        Implementors MAY raise NotImplementedError if dynamic client registration is
        disabled in ClientRegistrationOptions.

        Args:
            client_info: The client metadata to register.

        Raises:
            RegistrationError: If the client metadata is invalid.
        """
        self._dynamic_clients[client_info.client_id] = client_info

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """
        Called as part of the /authorize endpoint, and returns a URL that the client
        will be redirected to.
        Many MCP implementations will redirect to a third-party provider to perform
        a second OAuth exchange with that provider. In this sort of setup, the client
        has an OAuth connection with the MCP server, and the MCP server has an OAuth
        connection with the 3rd-party provider. At the end of this flow, the client
        should be redirected to the redirect_uri from params.redirect_uri.

        +--------+     +------------+     +-------------------+
        |        |     |            |     |                   |
        | Client | --> | MCP Server | --> | 3rd Party OAuth   |
        |        |     |            |     | Server            |
        +--------+     +------------+     +-------------------+
                            |   ^                  |
        +------------+      |   |                  |
        |            |      |   |    Redirect      |
        |redirect_uri|<-----+   +------------------+
        |            |
        +------------+

        Implementations will need to define another handler on the MCP server return
        flow to perform the second redirect, and generate and store an authorization
        code as part of completing the OAuth authorization step.

        Implementations SHOULD generate an authorization code with at least 160 bits of
        entropy,
        and MUST generate an authorization code with at least 128 bits of entropy.
        See https://datatracker.ietf.org/doc/html/rfc6749#section-10.10.

        Args:
            client: The client requesting authorization.
            params: The parameters of the authorization request.

        Returns:
            A URL to redirect the client to for authorization.

        Raises:
            AuthorizeError: If the authorization request is invalid.
        """
        state_id = params.state or secrets.token_hex(16)

        redirect_uri = client.validate_redirect_uri(params.redirect_uri)
        scopes = client.validate_scope(
            " ".join(params.scopes) if params.scopes else None
        )

        self._states[state_id] = YandexOAuthState(
            redirect_uri=redirect_uri,
            code_challenge=params.code_challenge,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            client_id=client.client_id,
            resource=params.resource,  # RFC 8707
        )

        return construct_redirect_uri(
            "https://oauth.yandex.ru/authorize",
            response_type="code",
            client_id=self._client_id,
            redirect_uri=str(self._server_url / "oauth/yandex/callback"),
            state=state_id,
            scope=" ".join(scopes) if scopes else None,
        )

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> YandexOauthAuthorizationCode | None:
        """
        Loads an AuthorizationCode by its code.

        Args:
            client: The client that requested the authorization code.
            authorization_code: The authorization code to get the challenge for.

        Returns:
            The AuthorizationCode, or None if not found
        """
        return self._auth_codes.get(authorization_code)

    def _save_oauth_token(
        self,
        token: OAuthToken,
        client: OAuthClientInformationFull,
        scopes: list[str],
        resource: str | None,
    ) -> None:
        """
        Helper method to save an OAuth token and its associated metadata.
        """
        assert token.expires_in is not None, "expires_in must be provided"

        self._tokens[token.access_token] = AccessToken(
            token=token.access_token,
            client_id=client.client_id,
            scopes=scopes,
            expires_at=int(time.time() + token.expires_in),
            resource=resource,
        )

        if token.refresh_token is not None:
            self._refresh_tokens[token.refresh_token] = RefreshToken(
                token=token.refresh_token,
                client_id=client.client_id,
                scopes=scopes,
            )

            self._refresh2access_tokens[token.refresh_token] = token.access_token

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: YandexOauthAuthorizationCode,
    ) -> OAuthToken:
        """
        Exchanges an authorization code for an access token and refresh token.

        Args:
            client: The client exchanging the authorization code.
            authorization_code: The authorization code to exchange.

        Returns:
            The OAuth token, containing access and refresh tokens.

        Raises:
            TokenError: If the request is invalid
        """
        if authorization_code.code not in self._auth_codes:
            raise ValueError("Invalid authorization code")

        del self._auth_codes[authorization_code.code]

        form = aiohttp.FormData()
        form.add_field("grant_type", "authorization_code")
        form.add_field("code", authorization_code.yandex_auth_code)
        form.add_field("client_id", self._client_id)
        form.add_field("client_secret", self._client_secret)
        form.add_field("redirect_uri", f"{str(self._server_url)}/oauth/yandex/callback")

        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                "https://oauth.yandex.ru/token", data=form
            ) as response:
                if response.status != 200:
                    raise ValueError("Failed to exchange authorization code")

                token = OAuthToken.model_validate_json(await response.read())
                assert token.expires_in is not None, "expires_in must be provided"

                self._save_oauth_token(
                    token=token,
                    client=client,
                    scopes=authorization_code.scopes,
                    resource=authorization_code.resource,
                )

                return token

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        """
        Loads a RefreshToken by its token string.

        Args:
            client: The client that is requesting to load the refresh token.
            refresh_token: The refresh token string to load.

        Returns:
            The RefreshToken object if found, or None if not found.
        """
        ref_token = self._refresh_tokens.get(refresh_token)
        if ref_token is None:
            return None

        if ref_token.expires_at and ref_token.expires_at < time.time():
            # Token is expired, remove it
            del self._refresh_tokens[refresh_token]
            return None

        return ref_token

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """
        Exchanges a refresh token for an access token and refresh token.

        Implementations SHOULD rotate both the access token and refresh token.

        Args:
            client: The client exchanging the refresh token.
            refresh_token: The refresh token to exchange.
            scopes: Optional scopes to request with the new access token.

        Returns:
            The OAuth token, containing access and refresh tokens.

        Raises:
            TokenError: If the request is invalid
        """
        form = aiohttp.FormData()
        form.add_field("grant_type", "refresh_token")
        form.add_field("refresh_token", refresh_token.token)
        form.add_field("client_id", self._client_id)
        form.add_field("client_secret", self._client_secret)

        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                "https://oauth.yandex.ru/token", data=form
            ) as response:
                if response.status != 200:
                    raise ValueError("Failed to refresh token")

                token = OAuthToken.model_validate_json(await response.read())
                assert token.expires_in is not None, "expires_in must be provided"

                ref_token = self._refresh_tokens[refresh_token.token]
                access_token_val = self._refresh2access_tokens.get(refresh_token.token)
                access_token = (
                    self._tokens.get(access_token_val) if access_token_val else None
                )

                del self._refresh_tokens[refresh_token.token]
                del self._refresh2access_tokens[refresh_token.token]
                if access_token_val:
                    del self._tokens[access_token_val]

                self._save_oauth_token(
                    token=token,
                    client=client,
                    scopes=ref_token.scopes,
                    resource=access_token.resource if access_token else None,
                )

                return token

    async def load_access_token(self, token: str) -> AccessToken | None:
        """
        Loads an access token by its token.

        Args:
            token: The access token to verify.

        Returns:
            The AuthInfo, or None if the token is invalid.
        """
        access_token = self._tokens.get(token)
        if not access_token:
            return None

        # Check if expired
        if access_token.expires_at and access_token.expires_at < time.time():
            del self._tokens[token]
            return None

        return access_token

    async def revoke_token(
        self,
        token: AccessToken | RefreshToken,
    ) -> None:
        """
        Revokes an access or refresh token.

        If the given token is invalid or already revoked, this method should do nothing.

        Implementations SHOULD revoke both the access token and its corresponding
        refresh token, regardless of which of the access token or refresh token is
        provided.

        Args:
            token: the token to revoke
        """
        raise NotImplementedError()
