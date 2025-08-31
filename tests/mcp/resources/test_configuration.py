from mcp.client.session import ClientSession
from mcp.types import TextResourceContents
from pydantic import AnyUrl


class TestConfigurationResource:
    async def test_read_returns_configuration(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.read_resource(
            AnyUrl("tracker-mcp://configuration")
        )

        assert len(result.contents) > 0
        # The content should be text containing configuration data
        content = result.contents[0]
        assert isinstance(content, TextResourceContents)
        assert content.text is not None

    async def test_contains_expected_fields(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.read_resource(
            AnyUrl("tracker-mcp://configuration")
        )

        content = result.contents[0]
        assert isinstance(content, TextResourceContents)
        content_text = content.text
        # Verify the configuration contains expected field names
        assert "read_only" in content_text
        assert "cache_enabled" in content_text
