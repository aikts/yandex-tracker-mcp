import secrets
import time

import aiohttp
import yarl
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.types import (
    YandexCallbackRequest,
    YandexOauthAuthorizationCode,
    YandexOAuthState,
)


class YandexOAuthAuthorizationServerProvider(
    OAuthAuthorizationServerProvider[
        YandexOauthAuthorizationCode, RefreshToken, AccessToken
    ]
):
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        server_url: yarl.URL,
        yandex_oauth_issuer: yarl.URL,
        store: OAuthStore,
        scopes: list[str] | None = None,
        use_scopes: bool = True,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._server_url = server_url
        self._yandex_oauth_issuer = yandex_oauth_issuer
        self._store = store
        self._scopes = scopes
        self._use_scopes = use_scopes

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

        state = await self._store.get_state(yandex_cb_data.state)
        if state is None:
            return JSONResponse(
                content="invalid state",
                status_code=400,
            )

        # Create MCP authorization code
        new_code = f"mcp_{secrets.token_hex(16)}"
        auth_code = YandexOauthAuthorizationCode(
            code=new_code,
            yandex_auth_code=yandex_cb_data.code,
            client_id=state.client_id,
            redirect_uri=state.redirect_uri,
            redirect_uri_provided_explicitly=state.redirect_uri_provided_explicitly,
            expires_at=time.time() + 300,
            scopes=state.scopes or self._scopes or [],
            code_challenge=state.code_challenge,
            resource=state.resource,  # RFC 8707
        )
        await self._store.save_auth_code(auth_code, ttl=300)

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
        return await self._store.get_client(client_id)

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
        await self._store.save_client(client_info)

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
        if self._use_scopes:
            scopes = client.validate_scope(
                " ".join(params.scopes) if params.scopes else None
            )
        else:
            scopes = None

        await self._store.save_state(
            YandexOAuthState(
                redirect_uri=redirect_uri,
                code_challenge=params.code_challenge,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                client_id=client.client_id,
                resource=params.resource,  # RFC 8707
                scopes=scopes,
            ),
            state_id=state_id,
            ttl=600,  # 10 minutes TTL for state
        )

        return construct_redirect_uri(
            str(self._yandex_oauth_issuer / "authorize"),
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
        return await self._store.get_auth_code(authorization_code)

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
        # Authorization codes are single-use and removed by get_auth_code

        form = aiohttp.FormData()
        form.add_field("grant_type", "authorization_code")
        form.add_field("code", authorization_code.yandex_auth_code)
        form.add_field("client_id", self._client_id)
        form.add_field("client_secret", self._client_secret)
        form.add_field("redirect_uri", str(self._server_url / "oauth/yandex/callback"))

        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                self._yandex_oauth_issuer / "token", data=form
            ) as response:
                if response.status != 200:
                    raise ValueError("Failed to exchange authorization code")

                token = OAuthToken.model_validate_json(await response.read())

                await self._store.save_oauth_token(
                    token=token,
                    client_id=client.client_id,
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
        return await self._store.get_refresh_token(refresh_token)

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
        # Get the existing refresh token to retrieve scopes

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

        # Revoke the old refresh token (and its associated access token)
        await self._store.revoke_refresh_token(refresh_token.token)

        # Save the new tokens
        await self._store.save_oauth_token(
            token=token,
            client_id=client.client_id,
            scopes=refresh_token.scopes,
            resource=None,
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
        return await self._store.get_access_token(token)

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
