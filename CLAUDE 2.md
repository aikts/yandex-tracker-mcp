# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Yandex Tracker is a Model Context Protocol (MCP) server that provides tools for interacting with Yandex Tracker API. It implements a FastMCP server with protocol-based architecture and optional Redis caching.

## Common Development Commands

```bash
# Install dependencies (using uv)
uv sync

# Run all checks (format, lint, type checking)
make

# Auto-format code
make format

# Run type checking
make mypy

# Update dependencies
make lock

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

Currently, the project doesn't have explicit test files. When adding tests:
- Use pytest as the testing framework
- Mock the protocol interfaces for unit testing
- Test both with and without caching enabled
- Verify queue restrictions are properly enforced

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
- Run `make` to ensure all checks pass
- Test the tool functionality
- Verify documentation is accurate and complete

## Committing

Before each commit it is mandatory to run:
```bash
make
```
