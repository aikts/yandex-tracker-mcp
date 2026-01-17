from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from mcp.client.session import ClientSession
from mcp.server import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.server import Lifespan, create_mcp_server
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol


@asynccontextmanager
async def safe_client_session(
    mcp_server: FastMCP[Any],
) -> AsyncIterator[ClientSession]:
    """Context manager wrapper that handles anyio teardown issues.

    The MCP SDK's create_connected_server_and_client_session uses anyio
    task groups that can fail during cleanup in pytest-asyncio environments.
    This wrapper suppresses those cleanup errors since the test has already
    completed successfully at that point.
    """
    ctx_mgr = create_connected_server_and_client_session(
        mcp_server, raise_exceptions=True
    )
    session = await ctx_mgr.__aenter__()
    try:
        yield session
    finally:
        with suppress(RuntimeError, ExceptionGroup):
            await ctx_mgr.__aexit__(None, None, None)


def get_tool_result_content(result: CallToolResult) -> Any:
    """Extract content from a tool result using structuredContent.

    FastMCP populates structuredContent with the tool's return value:
    - Single Pydantic model: structuredContent is the model dict directly
    - Primitives (str, int) and lists: structuredContent = {'result': value}

    Args:
        result: The CallToolResult from client_session.call_tool()

    Returns:
        The tool's return value (dict, list, str, int, etc.)
    """
    structured = result.structuredContent
    assert structured is not None, "Tool result has no structuredContent"

    # If structuredContent has a 'result' key, return that (primitives, lists)
    # Otherwise return the whole dict (single Pydantic model)
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    return structured


def create_test_settings(
    limit_queues: list[str] | None = None,
    read_only: bool = False,
) -> Settings:
    """Create Settings for testing with minimal required configuration."""
    return Settings.model_construct(
        tracker_token="test-token",
        tracker_org_id="test-org",
        tracker_cloud_org_id=None,
        tracker_limit_queues=limit_queues,
        tracker_read_only=read_only,
        tools_cache_enabled=False,
        oauth_enabled=False,
        host="0.0.0.0",
        port=8000,
        transport="stdio",
        tracker_api_base_url="https://api.tracker.yandex.net",
        tracker_iam_token=None,
        tracker_sa_key_id=None,
        tracker_sa_service_account_id=None,
        tracker_sa_private_key=None,
    )


@pytest.fixture
def test_settings() -> Settings:
    """Create Settings for testing with minimal required configuration."""
    return create_test_settings()


@pytest.fixture
def test_settings_with_queue_limits() -> Settings:
    """Settings with queue restrictions enabled."""
    return create_test_settings(limit_queues=["ALLOWED", "PERMITTED"])


@pytest.fixture
def mock_queues_protocol() -> AsyncMock:
    """Create a mock QueuesProtocol."""
    return AsyncMock(spec=QueuesProtocol)


@pytest.fixture
def mock_issues_protocol() -> AsyncMock:
    """Create a mock IssueProtocol."""
    return AsyncMock(spec=IssueProtocol)


@pytest.fixture
def mock_fields_protocol() -> AsyncMock:
    """Create a mock GlobalDataProtocol."""
    return AsyncMock(spec=GlobalDataProtocol)


@pytest.fixture
def mock_users_protocol() -> AsyncMock:
    """Create a mock UsersProtocol."""
    return AsyncMock(spec=UsersProtocol)


@pytest.fixture
def mock_app_context(
    mock_queues_protocol: AsyncMock,
    mock_issues_protocol: AsyncMock,
    mock_fields_protocol: AsyncMock,
    mock_users_protocol: AsyncMock,
) -> AppContext:
    """Create AppContext with mock protocols."""
    return AppContext(
        queues=mock_queues_protocol,
        issues=mock_issues_protocol,
        fields=mock_fields_protocol,
        users=mock_users_protocol,
    )


def make_test_lifespan(app_context: AppContext) -> Lifespan:
    """Create a test lifespan that yields the given AppContext."""

    @asynccontextmanager
    async def test_lifespan(_server: FastMCP[Any]) -> AsyncIterator[AppContext]:
        yield app_context

    return test_lifespan


@pytest.fixture
def mcp_server(test_settings: Settings, mock_app_context: AppContext) -> FastMCP[Any]:
    """Create test MCP server using the refactored create_mcp_server."""
    return create_mcp_server(
        settings=test_settings,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest.fixture
def mcp_server_with_queue_limits(
    test_settings_with_queue_limits: Settings,
    mock_app_context: AppContext,
) -> FastMCP[Any]:
    """Create test MCP server with queue restrictions."""
    return create_mcp_server(
        settings=test_settings_with_queue_limits,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest_asyncio.fixture(loop_scope="function")
async def client_session(
    mcp_server: FastMCP[Any],
) -> AsyncIterator[ClientSession]:
    """Create connected client session for testing MCP tools."""
    async with safe_client_session(mcp_server) as session:
        yield session


@pytest_asyncio.fixture(loop_scope="function")
async def client_session_with_limits(
    mcp_server_with_queue_limits: FastMCP[Any],
) -> AsyncIterator[ClientSession]:
    """Create connected client session with queue restrictions."""
    async with safe_client_session(mcp_server_with_queue_limits) as session:
        yield session


@pytest.fixture
def test_settings_read_only() -> Settings:
    """Settings with read-only mode enabled."""
    return create_test_settings(read_only=True)


@pytest.fixture
def mcp_server_read_only(
    test_settings_read_only: Settings,
    mock_app_context: AppContext,
) -> FastMCP[Any]:
    """Create test MCP server in read-only mode."""
    return create_mcp_server(
        settings=test_settings_read_only,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest_asyncio.fixture(loop_scope="function")
async def client_session_read_only(
    mcp_server_read_only: FastMCP[Any],
) -> AsyncIterator[ClientSession]:
    """Create connected client session for read-only server."""
    async with safe_client_session(mcp_server_read_only) as session:
        yield session
