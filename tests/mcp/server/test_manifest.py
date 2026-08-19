"""`manifest.json` advertises the full tool surface, so it must stay in sync with
what the server actually registers - including which tools need an opt-in flag."""

import json
from pathlib import Path
from typing import Any

import pytest
from mcp.client.session import ClientSession

from tests.mcp.server.test_server_creation import (
    ENTITY_READ_ONLY_TOOL_NAMES,
    ENTITY_WRITE_TOOL_NAMES,
)

ENTITIES_FLAG_NOTE = "(requires TRACKER_ENTITIES_ENABLED)"
MANIFEST_PATH = Path(__file__).parents[3] / "manifest.json"


@pytest.fixture(scope="module")
def manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


async def test_manifest_lists_every_registered_tool(
    manifest: dict[str, Any], client_session: ClientSession
) -> None:
    result = await client_session.list_tools()
    registered = {tool.name for tool in result.tools}
    listed = {tool["name"] for tool in manifest["tools"]}

    assert registered == listed


@pytest.mark.parametrize(
    "tool_name", ENTITY_READ_ONLY_TOOL_NAMES + ENTITY_WRITE_TOOL_NAMES
)
def test_entity_tools_are_marked_as_opt_in(
    manifest: dict[str, Any], tool_name: str
) -> None:
    """Entity tools are not registered by default, so the manifest must say so."""
    descriptions = {tool["name"]: tool["description"] for tool in manifest["tools"]}

    assert descriptions[tool_name].endswith(ENTITIES_FLAG_NOTE)


async def test_non_entity_tools_are_not_marked_as_opt_in(
    manifest: dict[str, Any], client_session_entities_disabled: ClientSession
) -> None:
    result = await client_session_entities_disabled.list_tools()
    always_registered = {tool.name for tool in result.tools}
    descriptions = {tool["name"]: tool["description"] for tool in manifest["tools"]}

    for name in always_registered:
        assert ENTITIES_FLAG_NOTE not in descriptions[name], (
            f"'{name}' is registered by default but the manifest marks it as opt-in"
        )


async def test_manifest_declares_the_entities_flag(manifest: dict[str, Any]) -> None:
    assert "tracker_entities_enabled" in manifest["user_config"]
    assert manifest["user_config"]["tracker_entities_enabled"]["default"] is False
    assert (
        manifest["server"]["mcp_config"]["env"]["TRACKER_ENTITIES_ENABLED"]
        == "${user_config.tracker_entities_enabled}"
    )
