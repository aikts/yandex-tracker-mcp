# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, etc.) when working with code in this repository.

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

- **Protocols** (`mcp_tracker/tracker/proto/`): Define API contracts (`QueuesProtocol`, `IssueProtocol`, `GlobalDataProtocol`, `TemplatesProtocol`, `UsersProtocol`), each exposed on `AppContext` as `queues` / `issues` / `fields` / `templates` / `users`
- **Client** (`mcp_tracker/tracker/custom/client.py`): Implements protocols, handles HTTP requests
- **Caching** (`mcp_tracker/tracker/caching/client.py`): Wraps protocols with Redis caching
- **MCP Server** (`mcp_tracker/mcp/server.py`): Server creation and configuration
- **MCP Tools** (`mcp_tracker/mcp/tools/`): Tool definitions organized by category
  - `_access.py`: Access control helpers (`check_issue_access`, `check_queue_access`)
  - `queue.py` / `queue_write.py`: Queue read-only / write tools
  - `field.py`: Global field and metadata tools (read-only)
  - `template.py`: Issue and comment template tools (read-only)
  - `board.py`: Board and sprint tools (read-only)
  - `issue_read.py` / `issue_write.py`: Issue read-only / write tools
  - `user.py`: User tools (read-only)
  - `__init__.py`: Exports `register_all_tools()` which orchestrates tool registration
  - `*_write.py` modules are only registered when `settings.tracker_read_only=False`
  - project/portfolio/goal modules are only registered when `settings.tracker_entities_enabled=True`
- **Settings** (`mcp_tracker/settings.py`): Pydantic settings from environment variables
- All protocol methods accept optional `auth: YandexAuth | None` parameter for OAuth support.
- All Pydantic models for Yandex Tracker entities inherit from `BaseTrackerEntity`.

### Writing to the Tracker API

- **Reference fields** (`type`, `priority`, `parent`, `sprint`, `followers`, `components`, `project`) use the shared models in `mcp_tracker/tracker/proto/types/inputs.py` (`Issue*Ref`), serialized by `_ref_body()` in the client. How Tracker resolves a bare value is per field, so check before widening a parameter: `type` / `priority` accept an id or a key and resolve a numeric string as an id (verified against the API), `followers` accept a uid or a login the same way, and a 422 from these means the referenced entity does not exist. `components` are the exception - a bare string there is a *name*, which makes a numeric-looking name ambiguous (this is what `components: ["694"]` answered 422 for), hence `IssueComponentRef` requiring exactly one of `id` / `name`. Create and update must accept and send the same value the same way - the API takes a bare key or id on both, so a parameter widened on one has to be widened on the other, or an agent that created an issue with a scalar hits a schema error when it updates the same way.
- **Errors**: use `await self._raise_for_status(response)` instead of `response.raise_for_status()` so Tracker's own `errorMessages` / `errors` end up in the raised `TrackerAPIError` (a bare "Unprocessable Entity" tells the caller nothing). Status codes with an actionable meaning get a dedicated error: 404 → `IssueNotFound` on issue-scoped paths, `QueueNotFound` on queue-scoped ones (`v3/queues/{queue}/...`) and `BoardNotFound` on board-scoped ones (`v3/boards/{board}/...`), 409 on update → `IssueVersionConflict`. A dedicated error applies to *every* method scoped to that entity, not just to newly added ones.
- **Field names on the wire**: a model may use a snake_case Python name, but it must accept *and emit* Tracker's own name - set `serialization_alias` next to every `validation_alias` (`story_points` reads and writes `storyPoints`). Responses are what callers feed back into `fields`, so the two spellings have to match; `tests/tracker/proto/test_model_aliases.py` fails if a new field forgets this.
- **`fields` maps**: `issue_create` / `issue_update` take the free-form map as an explicit `fields` parameter, never as `**kwargs` - a key naming a dedicated parameter used to raise `TypeError: got multiple values`. The client merges it into the body last, so an entry overrides the dedicated parameter and an explicit `null` clears the field (a dedicated parameter left as `None` is simply not sent).
- **Reference inputs**: every `Issue*Ref` validates that it carries something to resolve (`IssueComponentRef` wants exactly one of `id` / `name`, the others at least one of `id` / `key`); Tracker answers an empty object with an unhelpful 400/422, and when both `id` and `key` are set it resolves by `id`.
- **Issue `version`**: it is bumped by every change, including queue triggers and automation that fire right after creation, so the version returned by `issue_create` is routinely stale. Tools that accept `version` must say so and point at `issue_get` for a fresh read.
- **Templates are not applied on write** (decided 2026-08-17, not yet implemented): `POST /v3/issues` has no `templateId` parameter, so `issue_create` cannot take one without expanding the template client-side. Callers read `issue_template_get` and fill the arguments themselves. Adding a `template_id` parameter later means merging `fieldTemplates` under the explicit arguments (which win) and mapping its reference values onto the `Issue*Ref` models - the template returns them as objects like `{"id": "1", "key": "bug"}`, and `components` in particular need the id-or-name form (see the reference-fields note above). `checklistItems` / `metricItems` cannot be sent at creation at all and would need a follow-up request.

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

1. **Protocol**: Add method signature to the matching `mcp_tracker/tracker/proto/*.py` (a new protocol also needs a `*ProtocolWrap` base, a `CacheCollection` slot, an `AppContext` field and wiring in `make_tracker_lifespan`)
2. **Client**: Implement in `mcp_tracker/tracker/custom/client.py`
3. **Caching**: Add wrapper in `mcp_tracker/tracker/caching/client.py`
4. **Tool**: Add function to appropriate module in `mcp_tracker/mcp/tools/`:
   - Queue read-only tools → `queue.py`
   - Queue write tools → `queue_write.py`
   - Global field/metadata tools → `field.py`
   - Issue/comment template tools → `template.py`
   - Board/sprint tools → `board.py`
   - Issue read-only tools → `issue_read.py`
   - Issue write tools → `issue_write.py`
   - User tools → `user.py`
   - Project read-only tools → `project.py`; write tools → `project_write.py`
   - Portfolio read-only tools → `portfolio.py`; write tools → `portfolio_write.py`
   - Goal read-only tools → `goal.py`; write tools → `goal_write.py`
5. **Tests**: Add to appropriate `tests/mcp/tools/test_*_tools.py`
6. **Docs**: Update `README.md`, `README_ru.md`, and `manifest.json`

### Tool Categories

| Category | Module | Read-Only |
|----------|--------|-----------|
| Queue | `queue.py` | Yes |
| Queue Write | `queue_write.py` | No |
| Field | `field.py` | Yes |
| Template | `template.py` | Yes |
| Board | `board.py` | Yes |
| Issue Read | `issue_read.py` | Yes |
| Issue Write | `issue_write.py` | No |
| User | `user.py` | Yes |
| Project | `project.py` | Yes |
| Project Write | `project_write.py` | No |
| Portfolio | `portfolio.py` | Yes |
| Portfolio Write | `portfolio_write.py` | No |
| Goal | `goal.py` | Yes |
| Goal Write | `goal_write.py` | No |

**Write tools** (`*_write.py`) are only registered when `settings.tracker_read_only=False`.

**Entity tools** (project/portfolio/goal, read and write alike) are only registered when `settings.tracker_entities_enabled=True`.

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
- `TRACKER_LIMIT_QUEUES`: Restrict access to specific queues (allow-list, reads and writes)
- `TRACKER_READ_ONLY`: When `true`, disables all write tools (the `*_write.py` modules)
- `TRACKER_READ_ONLY_QUEUES`: Per-queue read-only allow-list. Write tools stay registered, but mutating calls targeting a listed queue are rejected via `check_*_access(..., write=True)` in `_access.py`; reads still work.
- `TRACKER_ENTITIES_ENABLED`: When `true`, registers the project/portfolio/goal tools (`project*.py`, `portfolio*.py`, `goal*.py`). Default `false`: they add a large tool manifest and are not covered by the queue restrictions above, since an entity isn't mappable to a single queue.
- `TOOLS_CACHE_ENABLED`: Enable Redis caching
- `OAUTH_ENABLED`: Enable OAuth provider mode
