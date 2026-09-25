"""`Settings` refuses a configuration that would expose the host's files.

`issue_add_attachment` uploads any file the server process can read, by a path the
client picks. That is the user's own machine over stdio, and anyone who can reach
the server - or a prompt injected into issue text - on a networked one.
"""

import os
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from mcp_tracker.settings import Settings

ENV_PREFIXES = ("TRACKER_", "OAUTH_", "MCP_", "TRANSPORT", "TOOLS_CACHE_")

# What OAuth mode needs to load at all, so that the file upload check is what fails.
OAUTH_SETTINGS: dict[str, Any] = {
    "oauth_enabled": True,
    "oauth_client_id": "client-id",
    "oauth_client_secret": "client-secret",
    "mcp_server_public_url": "https://mcp.example.com",
}


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep the developer's own environment and `.env` out of what these tests load."""
    monkeypatch.chdir(tmp_path)
    for name in [name for name in os.environ if name.startswith(ENV_PREFIXES)]:
        monkeypatch.delenv(name)


def load_settings(**overrides: Any) -> Settings:
    return Settings(
        tracker_token="test-token",
        tracker_org_id="test-org",
        **overrides,
    )


class TestFileUploadDefaults:
    def test_file_upload_is_off_by_default(self) -> None:
        assert load_settings().tracker_file_upload_enabled is False

    def test_upload_timeout_has_its_own_default(self) -> None:
        settings = load_settings()

        assert settings.tracker_upload_timeout == 300
        assert settings.tracker_upload_timeout > settings.tracker_api_timeout


class TestFileUploadTransportGuard:
    def test_accepted_on_stdio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRACKER_FILE_UPLOAD_ENABLED", "true")

        settings = load_settings()

        assert settings.transport == "stdio"
        assert settings.tracker_file_upload_enabled is True

    @pytest.mark.parametrize("transport", ["sse", "streamable-http"])
    def test_rejected_on_a_network_transport(
        self, monkeypatch: pytest.MonkeyPatch, transport: str
    ) -> None:
        monkeypatch.setenv("TRACKER_FILE_UPLOAD_ENABLED", "true")
        monkeypatch.setenv("TRANSPORT", transport)

        with pytest.raises(ValidationError) as exc_info:
            load_settings()

        message = str(exc_info.value)
        assert "TRACKER_FILE_UPLOAD_ENABLED" in message
        assert f"TRANSPORT={transport}" in message

    def test_rejected_in_oauth_mode(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            load_settings(tracker_file_upload_enabled=True, **OAUTH_SETTINGS)

        message = str(exc_info.value)
        assert "TRACKER_FILE_UPLOAD_ENABLED" in message
        assert "OAUTH_ENABLED=true" in message

    @pytest.mark.parametrize(
        "overrides",
        [
            pytest.param({"transport": "streamable-http"}, id="network-transport"),
            pytest.param(OAUTH_SETTINGS, id="oauth"),
        ],
    )
    def test_remote_servers_load_without_the_flag(
        self, overrides: dict[str, Any]
    ) -> None:
        assert load_settings(**overrides).tracker_file_upload_enabled is False
