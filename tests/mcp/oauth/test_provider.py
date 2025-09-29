import json
import time
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yarl
from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.types import (
    YandexOauthAuthorizationCode,
    YandexOAuthState,
)


class TestYandexOAuthAuthorizationServerProvider:
    @pytest.fixture
    def mock_store(self) -> Any:
        store = Mock(spec=OAuthStore)
        store.get_state = AsyncMock()
        store.save_state = AsyncMock()
        store.save_auth_code = AsyncMock()
        store.get_auth_code = AsyncMock()
        store.get_client = AsyncMock()
        store.save_client = AsyncMock()
        store.save_oauth_token = AsyncMock()
        store.get_access_token = AsyncMock()
        store.get_refresh_token = AsyncMock()
        store.revoke_refresh_token = AsyncMock()
        return store

    @pytest.fixture
    def provider(self, mock_store: Any) -> YandexOAuthAuthorizationServerProvider:
        return YandexOAuthAuthorizationServerProvider(
            client_id="test_client_id",
            client_secret="test_client_secret",
            server_url=yarl.URL("https://example.com"),
            yandex_oauth_issuer=yarl.URL("https://oauth.yandex.ru"),
            store=mock_store,
            scopes=["tracker:read", "tracker:write"],
        )

    @pytest.fixture
    def mock_client(self) -> Any:
        client = Mock(spec=OAuthClientInformationFull)
        client.client_id = "test_client_id"
        client.client_secret = "test_client_secret"
        client.redirect_uris = ["https://example.com/callback"]
        client.grant_types = ["authorization_code", "refresh_token"]
        client.response_types = ["code"]
        client.validate_redirect_uri = Mock(return_value="https://example.com/callback")
        client.validate_scope = Mock(return_value=["tracker:read"])
        return client

    async def test_handle_yandex_callback_success(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
    ) -> None:
        # Setup
        state_id = "test_state_id"
        auth_code = "test_auth_code"

        mock_state = YandexOAuthState(
            redirect_uri="https://example.com/callback",
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            client_id="test_client_id",
            scopes=["tracker:read"],
            resource=None,
        )

        mock_store.get_state.return_value = mock_state

        # Create mock request
        request = Mock(spec=Request)
        request.query_params = {"code": auth_code, "state": state_id}

        # Execute
        response = await provider.handle_yandex_callback(request)

        # Verify
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-store"

        # Verify store interactions
        mock_store.get_state.assert_called_once_with(state_id)
        mock_store.save_auth_code.assert_called_once()

        # Check the saved auth code
        saved_code = mock_store.save_auth_code.call_args[0][0]
        assert isinstance(saved_code, YandexOauthAuthorizationCode)
        assert saved_code.yandex_auth_code == auth_code
        assert saved_code.client_id == "test_client_id"
        assert saved_code.scopes == ["tracker:read"]

    async def test_handle_yandex_callback_invalid_params(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
    ) -> None:
        # Create mock request with invalid params
        request = Mock(spec=Request)
        request.query_params = {"invalid": "params"}

        # Execute
        response = await provider.handle_yandex_callback(request)

        # Verify
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert json.loads(response.body) == "invalid callback data"

    async def test_handle_yandex_callback_invalid_state(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
    ) -> None:
        # Setup
        mock_store.get_state.return_value = None

        request = Mock(spec=Request)
        request.query_params = {"code": "test_code", "state": "invalid_state"}

        # Execute
        response = await provider.handle_yandex_callback(request)

        # Verify
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert json.loads(response.body) == "invalid state"

    async def test_get_client(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_store.get_client.return_value = mock_client

        # Execute
        result = await provider.get_client("test_client_id")

        # Verify
        assert result == mock_client
        mock_store.get_client.assert_called_once_with("test_client_id")

    async def test_register_client(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        # Execute
        await provider.register_client(mock_client)

        # Verify
        mock_store.save_client.assert_called_once_with(mock_client)

    async def test_authorize(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        from mcp.server.auth.provider import AuthorizationParams

        # Setup
        params = AuthorizationParams(
            response_type="code",
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            scopes=["tracker:read"],
            state="test_state",
            code_challenge="test_challenge",
            code_challenge_method="S256",
            redirect_uri_provided_explicitly=True,
            resource="test_resource",
        )

        # Execute
        redirect_url = await provider.authorize(mock_client, params)

        # Verify
        assert redirect_url.startswith("https://oauth.yandex.ru/authorize")
        assert "response_type=code" in redirect_url
        assert "client_id=test_client_id" in redirect_url
        assert "redirect_uri=" in redirect_url
        assert "state=test_state" in redirect_url

        # Verify store interactions
        mock_store.save_state.assert_called_once()
        saved_state_args = mock_store.save_state.call_args
        saved_state = saved_state_args[0][0]
        assert isinstance(saved_state, YandexOAuthState)
        assert saved_state.client_id == "test_client_id"
        assert saved_state.scopes == ["tracker:read"]
        assert saved_state.resource == "test_resource"

    async def test_load_authorization_code(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_auth_code = YandexOauthAuthorizationCode(
            code="test_code",
            yandex_auth_code="yandex_code",
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
            scopes=["tracker:read"],
            code_challenge="test_challenge",
            resource=None,
        )
        mock_store.get_auth_code.return_value = mock_auth_code

        # Execute
        result = await provider.load_authorization_code(mock_client, "test_code")

        # Verify
        assert result == mock_auth_code
        mock_store.get_auth_code.assert_called_once_with("test_code")

    async def test_exchange_authorization_code_success(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_auth_code = YandexOauthAuthorizationCode(
            code="test_code",
            yandex_auth_code="yandex_code",
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
            scopes=["tracker:read"],
            code_challenge="test_challenge",
            resource="test_resource",
        )

        mock_token = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # Mock the entire HTTP exchange by patching the method directly
        with patch.object(
            provider,
            "exchange_authorization_code",
            wraps=provider.exchange_authorization_code,
        ):
            with patch("aiohttp.ClientSession") as mock_session_class:
                mock_response = Mock()
                mock_response.status = 200
                mock_response.read = AsyncMock(
                    return_value=json.dumps(mock_token).encode()
                )

                mock_context_manager = AsyncMock()
                mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
                mock_context_manager.__aexit__ = AsyncMock(return_value=None)

                mock_session = Mock()
                mock_session.post = Mock(return_value=mock_context_manager)

                mock_session_context = AsyncMock()
                mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_context.__aexit__ = AsyncMock(return_value=None)

                mock_session_class.return_value = mock_session_context

                # Execute
                result = await provider.exchange_authorization_code(
                    mock_client, mock_auth_code
                )

        # Verify
        assert isinstance(result, OAuthToken)
        assert result.access_token == "test_access_token"
        assert result.refresh_token == "test_refresh_token"

        # Verify store interactions
        mock_store.save_oauth_token.assert_called_once_with(
            token=result,
            client_id="test_client_id",
            scopes=["tracker:read"],
            resource="test_resource",
        )

    async def test_exchange_authorization_code_failure(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_auth_code = YandexOauthAuthorizationCode(
            code="test_code",
            yandex_auth_code="yandex_code",
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
            scopes=["tracker:read"],
            code_challenge="test_challenge",
            resource=None,
        )

        # Mock the entire HTTP exchange for failure case
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_response = Mock()
            mock_response.status = 400

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = Mock()
            mock_session.post = Mock(return_value=mock_context_manager)

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_context.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session_context

            # Execute & Verify
            with pytest.raises(
                ValueError, match="Failed to exchange authorization code"
            ):
                await provider.exchange_authorization_code(mock_client, mock_auth_code)

    async def test_load_refresh_token(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_refresh_token = RefreshToken(
            token="test_refresh_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )
        mock_store.get_refresh_token.return_value = mock_refresh_token

        # Execute
        result = await provider.load_refresh_token(mock_client, "test_refresh_token")

        # Verify
        assert result == mock_refresh_token
        mock_store.get_refresh_token.assert_called_once_with("test_refresh_token")

    async def test_exchange_refresh_token_success(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_refresh_token = RefreshToken(
            token="test_refresh_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )

        mock_token = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # Mock the entire HTTP exchange
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=json.dumps(mock_token).encode())

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = Mock()
            mock_session.post = Mock(return_value=mock_context_manager)

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_context.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session_context

            # Execute
            result = await provider.exchange_refresh_token(
                mock_client, mock_refresh_token, ["tracker:read"]
            )

        # Verify
        assert isinstance(result, OAuthToken)
        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"

        # Verify store interactions
        mock_store.revoke_refresh_token.assert_called_once_with("test_refresh_token")
        mock_store.save_oauth_token.assert_called_once_with(
            token=result,
            client_id="test_client_id",
            scopes=["tracker:read"],
            resource=None,
        )

    async def test_exchange_refresh_token_failure(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_client: Any,
    ) -> None:
        # Setup
        mock_refresh_token = RefreshToken(
            token="test_refresh_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )

        # Mock the entire HTTP exchange for failure case
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_response = Mock()
            mock_response.status = 400

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)

            mock_session = Mock()
            mock_session.post = Mock(return_value=mock_context_manager)

            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_context.__aexit__ = AsyncMock(return_value=None)

            mock_session_class.return_value = mock_session_context

            # Execute & Verify
            with pytest.raises(ValueError, match="Failed to refresh token"):
                await provider.exchange_refresh_token(
                    mock_client, mock_refresh_token, ["tracker:read"]
                )

    async def test_load_access_token(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
    ) -> None:
        # Setup
        mock_access_token = AccessToken(
            token="test_access_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )
        mock_store.get_access_token.return_value = mock_access_token  # type: ignore[attr-defined]

        # Execute
        result = await provider.load_access_token("test_access_token")

        # Verify
        assert result == mock_access_token
        mock_store.get_access_token.assert_called_once_with("test_access_token")  # type: ignore[attr-defined]

    async def test_revoke_token_not_implemented(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
    ) -> None:
        # Setup
        mock_access_token = AccessToken(
            token="test_access_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )

        # Execute & Verify
        with pytest.raises(NotImplementedError):
            await provider.revoke_token(mock_access_token)

    async def test_authorize_generates_state_when_none_provided(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
        mock_client: Any,
    ) -> None:
        from mcp.server.auth.provider import AuthorizationParams

        # Setup - no state provided
        params = AuthorizationParams(
            response_type="code",
            client_id="test_client_id",
            redirect_uri="https://example.com/callback",
            scopes=["tracker:read"],
            state=None,  # No state provided
            code_challenge="test_challenge",
            code_challenge_method="S256",
            redirect_uri_provided_explicitly=True,
            resource=None,
        )

        # Execute
        redirect_url = await provider.authorize(mock_client, params)

        # Verify that a state was generated
        assert "state=" in redirect_url
        mock_store.save_state.assert_called_once()

    async def test_handle_yandex_callback_uses_default_scopes_when_state_scopes_none(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Any,
    ) -> None:
        # Setup - state with None scopes should use provider's default scopes
        mock_state = YandexOAuthState(
            redirect_uri="https://example.com/callback",
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            client_id="test_client_id",
            scopes=None,  # None scopes
            resource=None,
        )

        mock_store.get_state.return_value = mock_state

        request = Mock(spec=Request)
        request.query_params = {"code": "test_code", "state": "test_state"}

        # Execute
        await provider.handle_yandex_callback(request)

        # Verify that default scopes were used
        saved_code = mock_store.save_auth_code.call_args[0][0]
        assert saved_code.scopes == [
            "tracker:read",
            "tracker:write",
        ]  # Default scopes from fixture
