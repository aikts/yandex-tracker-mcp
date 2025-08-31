import json
from unittest.mock import Mock

from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.types import (
    YandexOauthAuthorizationCode,
    YandexOAuthState,
)


class TestHandleYandexCallback:
    async def test_success(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
    ) -> None:
        state_id = "test_state_id"
        auth_code = "test_auth_code"

        mock_state = YandexOAuthState(
            redirect_uri=AnyHttpUrl("https://example.com/callback"),
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            client_id="test_client_id",
            scopes=["tracker:read"],
            resource=None,
        )

        mock_store.get_state.return_value = mock_state

        request = Mock(spec=Request)
        request.query_params = {"code": auth_code, "state": state_id}

        response = await provider.handle_yandex_callback(request)

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-store"

        # Verify redirect URL
        redirect_url = response.headers["Location"]
        assert redirect_url.startswith("https://example.com/callback?")
        assert f"state={state_id}" in redirect_url
        assert "code=" in redirect_url

        mock_store.get_state.assert_called_once_with(state_id)
        mock_store.save_auth_code.assert_called_once()

        saved_code = mock_store.save_auth_code.call_args[0][0]
        assert isinstance(saved_code, YandexOauthAuthorizationCode)
        assert saved_code.yandex_auth_code == auth_code
        assert saved_code.client_id == "test_client_id"
        assert saved_code.scopes == ["tracker:read"]

    async def test_invalid_params(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
    ) -> None:
        request = Mock(spec=Request)
        request.query_params = {"invalid": "params"}

        response = await provider.handle_yandex_callback(request)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert json.loads(bytes(response.body)) == "invalid callback data"

    async def test_invalid_state(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
    ) -> None:
        mock_store.get_state.return_value = None

        request = Mock(spec=Request)
        request.query_params = {"code": "test_code", "state": "invalid_state"}

        response = await provider.handle_yandex_callback(request)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert json.loads(bytes(response.body)) == "invalid state"

    async def test_uses_default_scopes_when_state_scopes_none(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
    ) -> None:
        mock_state = YandexOAuthState(
            redirect_uri=AnyHttpUrl("https://example.com/callback"),
            code_challenge="test_challenge",
            redirect_uri_provided_explicitly=True,
            client_id="test_client_id",
            scopes=None,
            resource=None,
        )

        mock_store.get_state.return_value = mock_state

        request = Mock(spec=Request)
        request.query_params = {"code": "test_code", "state": "test_state"}

        response = await provider.handle_yandex_callback(request)

        assert isinstance(response, RedirectResponse)
        redirect_url = response.headers["Location"]
        assert redirect_url.startswith("https://example.com/callback?")
        assert "state=test_state" in redirect_url

        saved_code = mock_store.save_auth_code.call_args[0][0]
        assert saved_code.scopes == ["tracker:read", "tracker:write"]
