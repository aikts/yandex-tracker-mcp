from unittest.mock import AsyncMock, Mock

import pytest
import yarl
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyHttpUrl

from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.store import OAuthStore


@pytest.fixture
def mock_store() -> Mock:
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
def provider(mock_store: Mock) -> YandexOAuthAuthorizationServerProvider:
    return YandexOAuthAuthorizationServerProvider(
        client_id="test_client_id",
        client_secret="test_client_secret",
        server_url=yarl.URL("https://example.com"),
        yandex_oauth_issuer=yarl.URL("https://oauth.yandex.ru"),
        store=mock_store,
        scopes=["tracker:read", "tracker:write"],
    )


@pytest.fixture
def client() -> OAuthClientInformationFull:
    return OAuthClientInformationFull(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uris=[AnyHttpUrl("https://example.com/callback")],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope="tracker:read",
    )
