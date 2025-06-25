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
uv run mcp-tracker stdio  # or sse
```

## Architecture

### Core Components

1. **Protocol-Based Design**: The codebase uses Python protocols (`mcp_tracker/tracker/proto/`) to define interfaces:
   - `IssueProtocol`, `QueuesProtocol`, `FieldsProtocol` define the API contracts
   - Implementations in `mcp_tracker/tracker/custom/client.py`
   - Caching layer in `mcp_tracker/tracker/caching/client.py` wraps the protocols

2. **Dependency Injection**: The FastMCP server uses lifespan context (`mcp_tracker/mcp/context.py`):
   - Protocols are instantiated in `tracker_lifespan` function
   - Dependencies injected into tool handlers via `ctx` parameter

3. **Configuration**: Managed through Pydantic settings (`mcp_tracker/settings.py`):
   - Environment variables loaded from `.env` file
   - Required: `TRACKER_TOKEN`, either `TRACKER_CLOUD_ORG_ID` or `TRACKER_ORG_ID`
   - Optional: Redis settings, queue restrictions, transport mode

4. **MCP Tools**: Defined in `mcp_tracker/mcp/server.py`:
   - Tools use strong typing with Pydantic models from `mcp_tracker/mcp/params.py`
   - Error handling through `mcp_tracker/mcp/errors.py`
   - Each tool interacts with Yandex Tracker via injected protocols

### Key Patterns

- **Type Safety**: All API responses modeled with Pydantic (`mcp_tracker/tracker/proto/types/`)
- **Caching**: Optional Redis caching applied via decorators in caching client
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
- Queue restrictions via `TRACKER_RESTRICTED_QUEUES`
- Caching behavior controlled by `TRACKER_ENABLE_CACHE`
- Transport modes: stdio (default) or sse
- Organization ID handling: cloud vs on-premise deployments

## Code Style

The project uses:
- Ruff for formatting and linting (configuration in `pyproject.toml`)
- MyPy for type checking with Pydantic plugin enabled
- Python 3.10+ features (union types with `|`)
- Comprehensive type hints throughout