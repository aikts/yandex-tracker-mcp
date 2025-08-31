import time
from unittest.mock import Mock

import pytest
from aioresponses import aioresponses
from mcp.server.auth.provider import AccessToken, RefreshToken
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl

from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.types import YandexOauthAuthorizationCode


class TestExchangeAuthorizationCode:
    async def test_success(
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
            resource="test_resource",
        )

        mock_token = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with aioresponses() as m:
            m.post(
                "https://oauth.yandex.ru/token",
                payload=mock_token,
                status=200,
            )

            result = await provider.exchange_authorization_code(client, mock_auth_code)

        assert isinstance(result, OAuthToken)
        assert result.access_token == "test_access_token"
        assert result.refresh_token == "test_refresh_token"

        mock_store.save_oauth_token.assert_called_once_with(
            token=result,
            client_id="test_client_id",
            scopes=["tracker:read"],
            resource="test_resource",
        )

    async def test_failure(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
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

        with aioresponses() as m:
            m.post(
                "https://oauth.yandex.ru/token",
                status=400,
            )

            with pytest.raises(
                ValueError, match="Failed to exchange authorization code"
            ):
                await provider.exchange_authorization_code(client, mock_auth_code)


class TestRefreshToken:
    async def test_load_refresh_token(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        mock_refresh_token = RefreshToken(
            token="test_refresh_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )
        mock_store.get_refresh_token.return_value = mock_refresh_token

        result = await provider.load_refresh_token(client, "test_refresh_token")

        assert result == mock_refresh_token
        mock_store.get_refresh_token.assert_called_once_with("test_refresh_token")

    async def test_exchange_success(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
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

        with aioresponses() as m:
            m.post(
                "https://oauth.yandex.ru/token",
                payload=mock_token,
                status=200,
            )

            result = await provider.exchange_refresh_token(
                client, mock_refresh_token, ["tracker:read"]
            )

        assert isinstance(result, OAuthToken)
        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"

        mock_store.revoke_refresh_token.assert_called_once_with("test_refresh_token")
        mock_store.save_oauth_token.assert_called_once_with(
            token=result,
            client_id="test_client_id",
            scopes=["tracker:read"],
            resource=None,
        )

    async def test_exchange_failure(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        client: OAuthClientInformationFull,
    ) -> None:
        mock_refresh_token = RefreshToken(
            token="test_refresh_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )

        with aioresponses() as m:
            m.post(
                "https://oauth.yandex.ru/token",
                status=400,
            )

            with pytest.raises(ValueError, match="Failed to refresh token"):
                await provider.exchange_refresh_token(
                    client, mock_refresh_token, ["tracker:read"]
                )


class TestAccessToken:
    async def test_load_access_token(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
    ) -> None:
        mock_access_token = AccessToken(
            token="test_access_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )
        mock_store.get_access_token.return_value = mock_access_token

        result = await provider.load_access_token("test_access_token")

        assert result == mock_access_token
        mock_store.get_access_token.assert_called_once_with("test_access_token")

    async def test_revoke_token_not_implemented(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
    ) -> None:
        mock_access_token = AccessToken(
            token="test_access_token",
            client_id="test_client_id",
            scopes=["tracker:read"],
        )

        with pytest.raises(NotImplementedError):
            await provider.revoke_token(mock_access_token)
