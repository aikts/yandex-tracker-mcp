# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Yandex Tracker is a Model Context Protocol (MCP) server that provides tools for interacting with Yandex Tracker API. It implements a FastMCP server with protocol-based architecture and optional Redis caching.

## Commands

```bash
task              # Run all checks (format, lint, type checking, tests) - REQUIRED before commits
task format       # Auto-format code
task check        # Run type and format checking
task test         # Run tests
uv sync           # Install dependencies
uv run mcp-tracker # Run the server
```

## Architecture

- **Protocols** (`mcp_tracker/tracker/proto/`): Define API contracts (`IssueProtocol`, `QueuesProtocol`, etc.)
- **Client** (`mcp_tracker/tracker/custom/client.py`): Implements protocols, handles HTTP requests
- **Caching** (`mcp_tracker/tracker/caching/client.py`): Wraps protocols with Redis caching
- **MCP Server** (`mcp_tracker/mcp/server.py`): Server creation and configuration
- **MCP Tools** (`mcp_tracker/mcp/tools/`): Tool definitions organized by category
  - `_access.py`: Access control helpers (`check_issue_access`, `check_queue_access`)
  - `queue.py`: Queue tools (5 read-only tools)
  - `field.py`: Global field/metadata tools (6 read-only tools)
  - `issue_read.py`: Issue read tools (9 read-only tools)
  - `issue_write.py`: Issue write tools (4 tools, conditional on `tracker_read_only`)
  - `user.py`: User tools (4 read-only tools)
  - `__init__.py`: Exports `register_all_tools()` which orchestrates tool registration
- **Settings** (`mcp_tracker/settings.py`): Pydantic settings from environment variables
- All protocol methods accept optional `auth: YandexAuth | None` parameter for OAuth support.
- All Pydantic models for Yandex Tracker entities inherit from `BaseTrackerEntity`.

## Testing

### Rules

- Use **pytest** with asyncio mode `auto`
- Use **aioresponses** for HTTP mocking in `TrackerClient` tests and `@tests/aioresponses_utils.py` for capturing request/response pairs.
- Use **AsyncMock** with `spec=` for protocol mocking in MCP tool tests
- Always type-hint all parameters including fixtures
- Never import inside functions - all imports at top of file
- Never use loops for test cases - use `@pytest.mark.parametrize`
- Use `model_construct()` for creating Pydantic model fixtures (skips validation)

### Test Locations

| What to test               | Where                                      |
|----------------------------|--------------------------------------------|
| TrackerClient HTTP methods | `tests/tracker/custom/test_*.py`           |
| Caching wrappers           | `tests/tracker/caching/test_*_protocol.py` |
| MCP tools                  | `tests/mcp/tools/test_*_tools.py`          |
| OAuth provider             | `tests/mcp/oauth/`                         |

### Testing TrackerClient (HTTP layer)

Use `aioresponses` to mock HTTP requests. Verify request headers and response parsing:

```python
async def test_api_method(self, client: TrackerClient) -> None:
    with aioresponses() as m:
        m.get("https://api.tracker.yandex.net/v3/endpoint", payload={"key": "value"})
        result = await client.api_method()
        assert result.key == "value"
```

### Testing MCP Tools

MCP tools are tested via `ClientSession.call_tool()` against a real `FastMCP` server with mocked protocols.

Key fixtures (from `tests/mcp/conftest.py`):
- `client_session`: Connected MCP client session
- `client_session_with_limits`: Session with queue restrictions enabled
- `mock_issues_protocol`, `mock_queues_protocol`, etc.: Mocked protocol instances

Use `get_tool_result_content(result)` helper to extract tool return values.

```python
async def test_tool(self, client_session: ClientSession, mock_issues_protocol: AsyncMock) -> None:
    mock_issues_protocol.issue_get.return_value = sample_issue
    result = await client_session.call_tool("issue_get", {"issue_id": "TEST-1"})
    assert not result.isError
    content = get_tool_result_content(result)
    assert content["key"] == "TEST-1"
```

For paginated methods, use `side_effect` for sequential returns: `mock.method.side_effect = [page1, []]`

## Adding New MCP Tools

### Implementation Checklist

1. **Protocol**: Add method signature to `mcp_tracker/tracker/proto/*.py`
2. **Client**: Implement in `mcp_tracker/tracker/custom/client.py`
3. **Caching**: Add wrapper in `mcp_tracker/tracker/caching/client.py`
4. **Tool**: Add function to appropriate module in `mcp_tracker/mcp/tools/`:
   - Queue tools → `queue.py`
   - Global field/metadata tools → `field.py`
   - Issue read-only tools → `issue_read.py`
   - Issue write tools → `issue_write.py`
   - User tools → `user.py`
5. **Tests**: Add to appropriate `tests/mcp/tools/test_*_tools.py`
6. **Docs**: Update `README.md`, `README_ru.md`, and `manifest.json`

### Tool Categories

| Category | Module | Read-Only | Description |
|----------|--------|-----------|-------------|
| Queue | `queue.py` | Yes | Queue listing, tags, versions, fields, metadata |
| Field | `field.py` | Yes | Global fields, statuses, types, priorities, resolutions |
| Issue Read | `issue_read.py` | Yes | Get, find, count issues; comments, links, worklogs, etc. |
| Issue Write | `issue_write.py` | No | Create, update, transition, close issues |
| User | `user.py` | Yes | List, search, get users |

**Write tools** in `issue_write.py` are only registered when `settings.tracker_read_only=False`.

### Test Requirements for New Tools

- Test success case with expected return data
- Test parameter passing (verify `call_args`)
- Test optional parameters (provided vs omitted)
- Test queue restrictions with `client_session_with_limits` if tool accesses issues/queues
- Add tool name to appropriate list in `tests/mcp/server/test_server_creation.py`:
  - Read-only tools → `READ_ONLY_TOOL_NAMES`
  - Write tools → `WRITE_TOOL_NAMES`
- For write tools, add test with `client_session_read_only` to verify not registered

## Configuration

Authentication (one required):
- `TRACKER_TOKEN`: Static OAuth token
- `TRACKER_IAM_TOKEN`: Static IAM token
- `TRACKER_SA_*`: Service account credentials for dynamic IAM tokens

Organization (one required):
- `TRACKER_CLOUD_ORG_ID`: For Yandex Cloud
- `TRACKER_ORG_ID`: For on-premise

Optional:
- `TRACKER_LIMIT_QUEUES`: Restrict access to specific queues
- `TRACKER_READ_ONLY`: When `true`, disables write tools (issue_create, issue_update, issue_close, issue_execute_transition)
- `TOOLS_CACHE_ENABLED`: Enable Redis caching
- `OAUTH_ENABLED`: Enable OAuth provider mode
