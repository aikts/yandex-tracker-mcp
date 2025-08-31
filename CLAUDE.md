# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Yandex Tracker is a Model Context Protocol (MCP) server that provides tools for interacting with Yandex Tracker API. It implements a FastMCP server with protocol-based architecture and optional Redis caching.

## Common Development Commands

```bash
# Install dependencies (using uv)
uv sync

# Run all checks (format, lint, type checking)
task

# Auto-format code
task format

# Run type checking
task mypy

# Update dependencies
task lock

# Run the server
uv run mcp-tracker

# Run with specific transport mode
uv run mcp-tracker stdio  # or streamable-http
```

## Architecture

### Core Components

1. **Protocol-Based Design**: The codebase uses Python protocols (`mcp_tracker/tracker/proto/`) to define interfaces:
   - `IssueProtocol`, `QueuesProtocol`, `GlobalDataProtocol` define the API contracts
   - Implementations in `mcp_tracker/tracker/custom/client.py`
   - Caching layer in `mcp_tracker/tracker/caching/client.py` wraps the protocols
   - All protocol methods now accept optional `auth` parameter for OAuth support

2. **Dependency Injection**: The FastMCP server uses lifespan context (`mcp_tracker/mcp/context.py`):
   - Protocols are instantiated in `tracker_lifespan` function
   - Dependencies injected into tool handlers via `ctx` parameter

3. **Configuration**: Managed through Pydantic settings (`mcp_tracker/settings.py`):
   - Environment variables loaded from `.env` file
   - Authentication (one required): `TRACKER_TOKEN`, `TRACKER_IAM_TOKEN`, or service account settings (`TRACKER_SA_*`)
   - Organization: either `TRACKER_CLOUD_ORG_ID` or `TRACKER_ORG_ID`
   - Optional: Redis settings, queue restrictions, transport mode, OAuth settings

4. **OAuth Provider**: When enabled, the server acts as an OAuth provider (`mcp_tracker/mcp/oauth.py`):
   - Implements OAuth 2.0 authorization code flow with PKCE support
   - Handles Yandex OAuth callbacks and token exchange
   - Manages refresh tokens and token lifecycle
   - Uses `YandexAuth` dataclass to encapsulate authentication data

5. **Authentication System**: Multi-tier authentication with priority order (`mcp_tracker/tracker/custom/client.py`):
   - **Dynamic OAuth Token** (highest priority): Token from OAuth flow passed via `auth` parameter
   - **Static OAuth Token**: Token from `TRACKER_TOKEN` environment variable
   - **Static IAM Token**: Token from `TRACKER_IAM_TOKEN` environment variable
   - **Dynamic IAM Token** (lowest priority): Generated from service account credentials (`TRACKER_SA_*`)
   - Authentication headers built in `_build_headers()` method following this priority
   - **Cache Consideration**: Cached results are shared across different auth contexts since cache keys don't include auth info

6. **Service Account Integration**: Support for Yandex Cloud service accounts (`mcp_tracker/tracker/custom/client.py`):
   - `ServiceAccountSettings` class handles service account configuration
   - `ServiceAccountStore` class manages IAM token lifecycle with automatic refresh
   - JWT-based authentication flow using private keys for token generation

7. **MCP Tools**: Defined in `mcp_tracker/mcp/server.py`:
   - Tools use strong typing with Pydantic models from `mcp_tracker/mcp/params.py`
   - Error handling through `mcp_tracker/mcp/errors.py`
   - Each tool interacts with Yandex Tracker via injected protocols

### Key Patterns

- **Type Safety**: All API responses modeled with Pydantic (`mcp_tracker/tracker/proto/types/`)
- **Base Entity**: All base Yandex Tracker entities (users, issues, etc.) must inherit from `BaseTrackerEntity` in `mcp_tracker/tracker/proto/types/base.py`. This base class handles the common `self` field that appears in all Yandex Tracker API responses.
- **Caching**: Optional Redis caching applied via decorators in caching client (cache key doesn't include auth, so different users share cached results)
- **Security**: Queue access restrictions enforced at the server level
- **Error Handling**: Custom exceptions for better error messages

## Testing Approach

### Testing Framework and Structure

The project uses **pytest** as the testing framework with the following configuration:
- Tests are located in the `tests/` directory
- Test files follow the pattern `test_*.py`
- Test classes follow the pattern `Test*`
- Test functions follow the pattern `test_*`
- Asyncio mode is set to `auto` in `pyproject.toml` for seamless async test support
- Verbose output with strict markers and short tracebacks enabled by default

### Directory Structure

Tests mirror the source code directory structure:
```
tests/
├── conftest.py                      # Root fixtures (TrackerClient instances)
├── protocol_utils.py                # Shared utilities for protocol testing
├── tracker/
│   ├── custom/
│   │   ├── conftest.py              # (none currently)
│   │   ├── test_client.py           # Client initialization tests
│   │   ├── test_auth.py             # Authentication header tests
│   │   ├── test_service_account.py  # Service account tests
│   │   ├── test_errors.py           # Error handling tests
│   │   ├── test_users_api.py        # Users API tests
│   │   ├── test_queues_api.py       # Queues API tests
│   │   ├── test_global_fields.py    # Global fields tests
│   │   ├── test_statuses.py         # Statuses tests
│   │   ├── test_issue_types.py      # Issue types tests
│   │   ├── test_priorities.py       # Priorities tests
│   │   └── issues/
│   │       ├── conftest.py          # Issue-specific fixtures (sample data)
│   │       ├── test_issue_get.py
│   │       ├── test_issues_find.py
│   │       ├── test_issues_count.py
│   │       ├── test_issue_comments.py
│   │       ├── test_issue_links.py
│   │       ├── test_issue_worklogs.py
│   │       ├── test_issue_attachments.py
│   │       └── test_issue_checklist.py
│   └── caching/
│       ├── test_users_protocol.py
│       ├── test_queues_protocol.py
│       ├── test_issues_protocol.py
│       └── test_global_data_protocol.py
└── mcp/
    ├── conftest.py                  # MCP-specific fixtures (mock protocols, settings)
    └── oauth/
        ├── test_provider.py
        └── stores/
            ├── test_memory.py
            └── test_redis.py
```

### Testing Principles

#### 1. **HTTP Request/Response Testing**
- Use **aioresponses** library for mocking HTTP requests
- Test that requests are properly formatted with correct headers, URLs, and payloads
- Verify responses are correctly parsed into Pydantic models
- Test error handling for different HTTP status codes

#### 2. **Dependency Injection Over Mocking**
- **Prefer dependency injection**: Pass test dependencies directly rather than using mocking libraries
- **Use mocking sparingly**: Only when it's the cleanest and most appropriate solution
- **Protocol-based testing**: Test against protocol interfaces rather than concrete implementations

#### 3. **Unit Testing Best Practices**
- **Focused tests**: Each test should verify one specific behavior
- **Concise**: Keep tests short and readable
- **Independent**: Tests should not depend on each other
- **Fast**: Unit tests should run quickly without external dependencies

#### 4. **Test Coverage Requirements**
- Verify queue access restrictions are properly enforced
- Test error conditions and exception handling
- Test edge cases like network timeouts, invalid responses
- Verify authentication header construction for all methods

#### 5. **Fixture Organization**
- **Root `conftest.py`**: Contains shared fixtures like `client` (TrackerClient instance)
- **Module-level `conftest.py`**: Contains fixtures specific to a test module (e.g., `tests/tracker/custom/issues/conftest.py` has sample issue data)
- **`tests/mcp/conftest.py`**: Contains mock protocol implementations and test settings for MCP server testing
- **`tests/protocol_utils.py`**: Shared utilities for protocol compliance testing

#### 6. **Code Style**
- Always use **pytest-mock** (`MockerFixture`) for mocking dependencies
- `unittest.mock.AsyncMock` may be used directly when creating simple mock objects in fixtures
- Always use type-hinting for all parameters in tests (including fixtures)
- **Never use imports inside functions**: All imports must be at the top of the file, never inside test functions or fixtures
- **Never use loops for test cases**: Always use `pytest.mark.parametrize` for running multiple test cases with different inputs:
  ```python
  @pytest.mark.parametrize("input_value,expected", [
      ("value1", "result1"),
      ("value2", "result2"),
  ])
  def test_function(input_value: str, expected: str) -> None:
      assert process(input_value) == expected
  ```

### Common Test Patterns

#### Testing HTTP API Methods (with aioresponses)
```python
from aioresponses import aioresponses
from mcp_tracker.tracker.custom.client import TrackerClient

class TestApiMethod:
    async def test_success(self, client: TrackerClient, sample_data: dict[str, Any]) -> None:
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/endpoint", payload=sample_data)
            result = await client.api_method()
            assert result.field == sample_data["field"]

    async def test_with_auth(self, client: TrackerClient, sample_data: dict[str, Any]) -> None:
        auth = YandexAuth(token="auth-token", org_id="auth-org")
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/endpoint", payload=sample_data)
            result = await client.api_method(auth=auth)
            # Verify headers
            request = m.requests[list(m.requests.keys())[0]][0]
            assert request.kwargs["headers"]["Authorization"] == "OAuth auth-token"
```

#### Testing Caching Protocol Wrappers
```python
from unittest.mock import AsyncMock

class TestCachingProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.method.return_value = SomeModel(...)
        return original

    async def test_calls_original(self, caching_protocol: Any, mock_original: AsyncMock) -> None:
        result = await caching_protocol.method(arg="value")
        mock_original.method.assert_called_once_with(arg="value", auth=None)
```

#### Testing with pytest-mock (MockerFixture)
```python
from pytest_mock import MockerFixture

class TestWithMocking:
    async def test_external_dependency(self, mocker: MockerFixture) -> None:
        mock_sdk = mocker.patch("module.path.ExternalSDK")
        mock_sdk.return_value.method.return_value = "result"
        # Test code that uses ExternalSDK
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=mcp_tracker

# Run tests for specific module
uv run pytest tests/tracker/custom/

# Run a specific test file
uv run pytest tests/tracker/custom/test_auth.py

# Run a specific test class
uv run pytest tests/tracker/custom/test_auth.py::TestOAuthAuthentication

# Run a specific test
uv run pytest tests/tracker/custom/test_auth.py::TestOAuthAuthentication::test_build_headers_oauth_from_auth_param

# Run tests matching a keyword
uv run pytest -k "auth"
```

## Important Configuration

When modifying the server, be aware of:

### Authentication Configuration
- **OAuth Token**: `TRACKER_TOKEN` - Static OAuth token for all requests
- **IAM Token**: `TRACKER_IAM_TOKEN` - Static IAM token for service-to-service auth
- **Service Account**: `TRACKER_SA_KEY_ID`, `TRACKER_SA_SERVICE_ACCOUNT_ID`, `TRACKER_SA_PRIVATE_KEY` - Dynamic IAM token generation
- **OAuth Provider Mode**: When `OAUTH_ENABLED=true`:
  - `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`: Yandex OAuth app credentials
  - `MCP_SERVER_PUBLIC_URL`: Public URL for OAuth callbacks
  - `OAUTH_STORE`: Storage backend (`memory` or `redis`)

### Other Configuration
- Queue restrictions via `TRACKER_LIMIT_QUEUES`
- Caching behavior controlled by `TOOLS_CACHE_ENABLED`
- Transport modes: stdio (default) or streamable-http
- Organization ID handling: cloud vs on-premise deployments (`TRACKER_CLOUD_ORG_ID` vs `TRACKER_ORG_ID`)
- In HTTP transport mode, org IDs can be passed via query parameters

## Code Style

The project uses:
- Ruff for formatting and linting (configuration in `pyproject.toml`)
- MyPy for type checking with Pydantic plugin enabled
- Python 3.10+ features (union types with `|`)
- Comprehensive type hints throughout

## Adding New MCP Tools

When adding new MCP tools, follow this comprehensive checklist:

### Implementation Steps
1. **Protocol Interface**: Add method to the appropriate protocol in `mcp_tracker/tracker/proto/` (e.g., `users.py`, `issues.py`)
2. **Client Implementation**: Implement the method in `mcp_tracker/tracker/custom/client.py`
3. **Caching Support**: Add caching wrapper in `mcp_tracker/tracker/caching/client.py`
4. **MCP Tool**: Add the tool function in `mcp_tracker/mcp/server.py` with proper typing and error handling
5. **Parameters**: If needed, add parameter models to `mcp_tracker/mcp/params.py`

### Documentation Requirements (MANDATORY)
**Always update these files when adding new tools:**

1. **README.md**: Add tool documentation in the appropriate section:
   - Tool name and description
   - Parameters with types and examples
   - Return value description
   - Usage notes or restrictions

2. **README_ru.md**: Add Russian translation of the tool documentation
   - Ensure it matches the English version

3. **manifest.json**: Add tool entry to the `tools` array:
   - Include `name` and `description` fields
   - Ensure description matches the MCP tool decorator

### Example Pattern
```python
# 1. Protocol (e.g., users.py)
async def user_get_current(self, *, auth: YandexAuth | None = None) -> User: ...

# 2. Client implementation
async def user_get_current(self, *, auth: YandexAuth | None = None) -> User:
    async with self._session.get(
        "v3/myself", headers=await self._build_headers(auth)
    ) as response:
        response.raise_for_status()
        return User.model_validate_json(await response.read())

# 3. Caching wrapper (passes auth to original but doesn't use it for cache key)
@cached(**cache_config)
async def user_get_current(self, *, auth: YandexAuth | None = None) -> User:
    return await self._original.user_get_current(auth=auth)

# 4. MCP tool
@mcp.tool(description="Get information about the current authenticated user")
async def user_get_current(ctx: Context[Any, AppContext]) -> User:
    return await ctx.request_context.lifespan_context.users.user_get_current(
        auth=get_yandex_auth(ctx)
    )
```

### Verification
- Run `task` to ensure all checks pass
- Test the tool functionality
- Verify documentation is accurate and complete

## Committing

Before each commit it is mandatory to run:
```bash
task
```
