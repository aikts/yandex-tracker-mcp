"""The tools the server registers, as an MCP client sees them.

Listing them runs no lifespan, so the server is built once at import time and the
tests that check a per-tool rule can parametrize over the result - which is what
makes one bad tool report as its own failing case.
"""

import asyncio

from mcp.types import Tool

from mcp_tracker.mcp.server import create_mcp_server
from tests.mcp.conftest import create_test_settings

REGISTERED_TOOLS: list[Tool] = asyncio.run(
    create_mcp_server(settings=create_test_settings()).list_tools()
)
TOOL_NAMES = frozenset(tool.name for tool in REGISTERED_TOOLS)
