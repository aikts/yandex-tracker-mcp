import time
from unittest.mock import Mock

import yarl
from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyHttpUrl

from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.types import (
    YandexOauthAuthorizationCode,
    YandexOAuthState,
)


class TestAuthorize:
    async def test_builds_correct_yandex_oauth_url(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        params = AuthorizationParams(
            redirect_uri=AnyHttpUrl("https://example.com/callback"),
            scopes=["tracker:read"],
            state="test_state",
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            resource="test_resource",
        )

        redirect_url = await provider.authorize(client, params)

        assert redirect_url.startswith("https://oauth.yandex.ru/authorize")
        assert "response_type=code" in redirect_url
        assert "client_id=test_client_id" in redirect_url
        assert "redirect_uri=" in redirect_url
        assert "state=test_state" in redirect_url

        mock_store.save_state.assert_called_once()
        saved_state_args = mock_store.save_state.call_args
        saved_state = saved_state_args[0][0]
        assert isinstance(saved_state, YandexOAuthState)
        assert saved_state.client_id == "test_client_id"
        assert saved_state.scopes == ["tracker:read"]
        assert saved_state.resource == "test_resource"

    async def test_skips_scope_validation_when_use_scopes_disabled(
        self,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        provider = YandexOAuthAuthorizationServerProvider(
            client_id="test_client_id",
            client_secret="test_client_secret",
            server_url=yarl.URL("https://example.com"),
            yandex_oauth_issuer=yarl.URL("https://oauth.yandex.ru"),
            store=mock_store,
            use_scopes=False,
        )
        params = AuthorizationParams(
            redirect_uri=AnyHttpUrl("https://example.com/callback"),
            scopes=["tracker:read"],
            state="test_state",
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            resource=None,
        )

        redirect_url = await provider.authorize(client, params)

        assert "scope=" not in redirect_url
        mock_store.save_state.assert_called_once()
        saved_state = mock_store.save_state.call_args[0][0]
        assert isinstance(saved_state, YandexOAuthState)
        assert saved_state.scopes is None

    async def test_generates_state_when_none_provided(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        params = AuthorizationParams(
            redirect_uri=AnyHttpUrl("https://example.com/callback"),
            scopes=["tracker:read"],
            state=None,
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            resource=None,
        )

        redirect_url = await provider.authorize(client, params)

        assert "state=" in redirect_url
        mock_store.save_state.assert_called_once()


class TestLoadAuthorizationCode:
    async def test_loads_code_from_store(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        mock_auth_code = YandexOauthAuthorizationCode(
            code="test_code",
            yandex_auth_code="yandex_code",
            client_id="test_client_id",
            redirect_uri=AnyHttpUrl("https://example.com/callback"),
            redirect_uri_provided_explicitly=True,
            expires_at=time.time() + 300,
            scopes=["tracker:read"],
            code_challenge="test_challenge",
            resource=None,
        )
        mock_store.get_auth_code.return_value = mock_auth_code

        result = await provider.load_authorization_code(client, "test_code")

        assert result == mock_auth_code
        mock_store.get_auth_code.assert_called_once_with("test_code")
