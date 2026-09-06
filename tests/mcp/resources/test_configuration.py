import json
from collections.abc import Sequence

import pytest
from mcp import Client
from mcp.types import TextResourceContents

CONFIGURATION_URI = "tracker-mcp://configuration"


def _configuration_text(contents: Sequence[object]) -> str:
    assert len(contents) > 0
    content = contents[0]
    assert isinstance(content, TextResourceContents)
    assert content.text is not None
    return content.text


class TestConfigurationResource:
    async def test_read_returns_configuration(
        self,
        client_session: Client,
    ) -> None:
        result = await client_session.read_resource(CONFIGURATION_URI)

        # The content should be text containing configuration data
        assert _configuration_text(result.contents)

    async def test_contains_expected_fields(
        self,
        client_session: Client,
    ) -> None:
        result = await client_session.read_resource(CONFIGURATION_URI)

        content_text = _configuration_text(result.contents)
        # Verify the configuration contains expected field names
        assert "read_only" in content_text
        assert "cache_enabled" in content_text

    async def test_plain_uri_reports_the_configured_organization(
        self,
        client_session: Client,
    ) -> None:
        """Without a query variable the template still matches and the
        settings' organization is what comes back."""
        result = await client_session.read_resource(CONFIGURATION_URI)

        configuration = json.loads(_configuration_text(result.contents))
        assert configuration["cloud_org_id"] is None
        assert configuration["org_id"] == "test-org"

    @pytest.mark.parametrize(
        ("query", "field", "other_field", "other_value"),
        [
            ("?cloudOrgId=from-uri", "cloud_org_id", "org_id", "test-org"),
            ("?orgId=from-uri", "org_id", "cloud_org_id", None),
        ],
        ids=["cloudOrgId", "orgId"],
    )
    async def test_query_variable_overrides_the_organization(
        self,
        client_session: Client,
        query: str,
        field: str,
        other_field: str,
        other_value: str | None,
    ) -> None:
        """The resource is a template: a query variable in the URI wins over
        settings, and the other organization field keeps its settings value."""
        result = await client_session.read_resource(f"{CONFIGURATION_URI}{query}")

        configuration = json.loads(_configuration_text(result.contents))
        assert configuration[field] == "from-uri"
        assert configuration[other_field] == other_value
