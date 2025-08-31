from unittest.mock import Mock

from mcp.shared.auth import OAuthClientInformationFull

from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider


class TestClientManagement:
    async def test_get_client(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        mock_store.get_client.return_value = client

        result = await provider.get_client("test_client_id")

        assert result == client
        mock_store.get_client.assert_called_once_with("test_client_id")

    async def test_register_client(
        self,
        provider: YandexOAuthAuthorizationServerProvider,
        mock_store: Mock,
        client: OAuthClientInformationFull,
    ) -> None:
        await provider.register_client(client)

        mock_store.save_client.assert_called_once_with(client)
