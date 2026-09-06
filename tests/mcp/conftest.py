import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from mcp import Client
from mcp.client.session import ElicitationFnT
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.server import Lifespan, create_mcp_server
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.boards import BoardsProtocol
from mcp_tracker.tracker.proto.components import ComponentsProtocol
from mcp_tracker.tracker.proto.entities import EntitiesProtocol
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.templates import TemplatesProtocol
from mcp_tracker.tracker.proto.types.pagination import PaginatedResult
from mcp_tracker.tracker.proto.users import UsersProtocol


@asynccontextmanager
async def safe_client_session(
    mcp_server: MCPServer[AppContext],
    elicitation_callback: ElicitationFnT | None = None,
) -> AsyncIterator[Client]:
    """Connect an in-process `Client` to the server for the duration of a test.

    `Client(server)` negotiates the modern (2026-07-28) protocol by default and
    dispatches directly without JSON-RPC framing; `raise_exceptions=True` makes a
    crash outside a tool body surface with its real text instead of a bare
    JSON-RPC error.

    The client is entered and exited inside one dedicated task: pytest-asyncio
    runs an async fixture's setup and teardown in separate tasks, and the anyio
    task group the in-process connection keeps its server side in refuses to be
    exited from a task other than the one that entered it.
    """
    ready: asyncio.Future[Client] = asyncio.get_running_loop().create_future()
    done = asyncio.Event()

    async def run() -> None:
        try:
            async with Client(
                mcp_server,
                raise_exceptions=True,
                elicitation_callback=elicitation_callback,
            ) as client:
                ready.set_result(client)
                await done.wait()
        except BaseException as exc:
            if not ready.done():
                ready.set_exception(exc)
            raise

    task = asyncio.create_task(run())
    try:
        yield await ready
    finally:
        done.set()
        await task


def page(
    values: list[Any], *, hits: int | None = None, pages: int | None = None
) -> PaginatedResult[Any]:
    """Wrap a list of items the way a paginated protocol method returns them."""
    return PaginatedResult[Any](values=values, hits=hits, pages=pages)


def get_tool_result_content(result: CallToolResult) -> Any:
    """Extract content from a tool result using structured_content.

    MCPServer populates structured_content with the tool's return value:
    - Single Pydantic model: structured_content is the model dict directly
    - Primitives (str, int) and lists: structured_content = {'result': value}

    Args:
        result: The CallToolResult from client_session.call_tool()

    Returns:
        The tool's return value (dict, list, str, int, etc.)
    """
    structured = result.structured_content
    assert structured is not None, "Tool result has no structured_content"

    # If structured_content has a 'result' key, return that (primitives, lists)
    # Otherwise return the whole dict (single Pydantic model)
    if isinstance(structured, dict) and "result" in structured:
        return structured["result"]
    return structured


def create_test_settings(
    limit_queues: list[str] | None = None,
    read_only: bool = False,
    read_only_queues: list[str] | None = None,
    entities_enabled: bool = True,
) -> Settings:
    """Create Settings for testing with minimal required configuration.

    `model_construct` skips validation, so the queue lists go through
    `decode_queue_keys` explicitly - tests must see the same normalised sets a
    real load produces, not the raw lists they were written with.
    """
    return Settings.model_construct(
        tracker_token="test-token",
        tracker_org_id="test-org",
        tracker_cloud_org_id=None,
        tracker_limit_queues=Settings.decode_queue_keys(limit_queues),
        tracker_read_only=read_only,
        tracker_read_only_queues=Settings.decode_queue_keys(read_only_queues),
        tracker_entities_enabled=entities_enabled,
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
def mock_templates_protocol() -> AsyncMock:
    """Create a mock TemplatesProtocol."""
    return AsyncMock(spec=TemplatesProtocol)


@pytest.fixture
def mock_users_protocol() -> AsyncMock:
    """Create a mock UsersProtocol."""
    return AsyncMock(spec=UsersProtocol)


@pytest.fixture
def mock_entities_protocol() -> AsyncMock:
    """Create a mock EntitiesProtocol."""
    return AsyncMock(spec=EntitiesProtocol)


@pytest.fixture
def mock_boards_protocol() -> AsyncMock:
    """Create a mock BoardsProtocol."""
    return AsyncMock(spec=BoardsProtocol)


@pytest.fixture
def mock_components_protocol() -> AsyncMock:
    """Create a mock ComponentsProtocol."""
    return AsyncMock(spec=ComponentsProtocol)


@pytest.fixture
def mock_app_context(
    mock_queues_protocol: AsyncMock,
    mock_issues_protocol: AsyncMock,
    mock_fields_protocol: AsyncMock,
    mock_templates_protocol: AsyncMock,
    mock_users_protocol: AsyncMock,
    mock_entities_protocol: AsyncMock,
    mock_boards_protocol: AsyncMock,
    mock_components_protocol: AsyncMock,
) -> AppContext:
    """Create AppContext with mock protocols."""
    return AppContext(
        queues=mock_queues_protocol,
        issues=mock_issues_protocol,
        fields=mock_fields_protocol,
        templates=mock_templates_protocol,
        users=mock_users_protocol,
        entities=mock_entities_protocol,
        boards=mock_boards_protocol,
        components=mock_components_protocol,
    )


def make_test_lifespan(app_context: AppContext) -> Lifespan:
    """Create a test lifespan that yields the given AppContext."""

    @asynccontextmanager
    async def test_lifespan(
        _server: MCPServer[AppContext],
    ) -> AsyncIterator[AppContext]:
        yield app_context

    return test_lifespan


@pytest.fixture
def mcp_server(
    test_settings: Settings, mock_app_context: AppContext
) -> MCPServer[AppContext]:
    """Create test MCP server using the refactored create_mcp_server."""
    return create_mcp_server(
        settings=test_settings,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest.fixture
def mcp_server_with_queue_limits(
    test_settings_with_queue_limits: Settings,
    mock_app_context: AppContext,
) -> MCPServer[AppContext]:
    """Create test MCP server with queue restrictions."""
    return create_mcp_server(
        settings=test_settings_with_queue_limits,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest_asyncio.fixture(loop_scope="function")
async def client_session(
    mcp_server: MCPServer[AppContext],
) -> AsyncIterator[Client]:
    """Create connected client session for testing MCP tools."""
    async with safe_client_session(mcp_server) as session:
        yield session


@pytest_asyncio.fixture(loop_scope="function")
async def client_session_with_limits(
    mcp_server_with_queue_limits: MCPServer[AppContext],
) -> AsyncIterator[Client]:
    """Create connected client session with queue restrictions."""
    async with safe_client_session(mcp_server_with_queue_limits) as session:
        yield session


@pytest.fixture
def test_settings_entities_disabled() -> Settings:
    """Settings with the default (opt-out) entity tool configuration."""
    return create_test_settings(entities_enabled=False)


@pytest.fixture
def mcp_server_entities_disabled(
    test_settings_entities_disabled: Settings,
    mock_app_context: AppContext,
) -> MCPServer[AppContext]:
    """Create test MCP server without project/portfolio/goal tools."""
    return create_mcp_server(
        settings=test_settings_entities_disabled,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest_asyncio.fixture(loop_scope="function")
async def client_session_entities_disabled(
    mcp_server_entities_disabled: MCPServer[AppContext],
) -> AsyncIterator[Client]:
    """Create connected client session with entity tools disabled."""
    async with safe_client_session(mcp_server_entities_disabled) as session:
        yield session


@pytest.fixture
def test_settings_with_read_only_queues() -> Settings:
    """Settings with per-queue read-only access configured.

    Write tools are registered globally, but mutations targeting a queue in
    ``tracker_read_only_queues`` are rejected. ``READONLY`` is read-only while
    other queues (e.g. ``TEST``) remain read-write.
    """
    return create_test_settings(read_only_queues=["READONLY"])


@pytest.fixture
def mcp_server_with_read_only_queues(
    test_settings_with_read_only_queues: Settings,
    mock_app_context: AppContext,
) -> MCPServer[AppContext]:
    """Create test MCP server with per-queue read-only access."""
    return create_mcp_server(
        settings=test_settings_with_read_only_queues,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest_asyncio.fixture(loop_scope="function")
async def client_session_with_read_only_queues(
    mcp_server_with_read_only_queues: MCPServer[AppContext],
) -> AsyncIterator[Client]:
    """Create connected client session with per-queue read-only access."""
    async with safe_client_session(mcp_server_with_read_only_queues) as session:
        yield session


@pytest.fixture
def test_settings_read_only() -> Settings:
    """Settings with read-only mode enabled."""
    return create_test_settings(read_only=True)


@pytest.fixture
def mcp_server_read_only(
    test_settings_read_only: Settings,
    mock_app_context: AppContext,
) -> MCPServer[AppContext]:
    """Create test MCP server in read-only mode."""
    return create_mcp_server(
        settings=test_settings_read_only,
        lifespan=make_test_lifespan(mock_app_context),
    )


@pytest_asyncio.fixture(loop_scope="function")
async def client_session_read_only(
    mcp_server_read_only: MCPServer[AppContext],
) -> AsyncIterator[Client]:
    """Create connected client session for read-only server."""
    async with safe_client_session(mcp_server_read_only) as session:
        yield session
