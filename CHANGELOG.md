# Changelog

All notable changes to this project will be documented in this file.

## [0.8.1-dev] - unreleased

### Bug Fixes

- With `TOOLS_CACHE_ENABLED=true`, the caller's raw OAuth/IAM token no longer ends up in the Redis cache key. aiocache builds keys by stringifying the cached method's arguments, so `YandexAuth`'s repr wrote the token verbatim into a namespace visible to `KEYS`/`SCAN`/`MONITOR`, RDB dumps and per-key metrics; secret fields now render as a SHA-256 fingerprint, which keeps entries distinct per caller and stops the token leaking into logs and tracebacks too
  - Cache entries written by earlier versions become misses and expire by TTL

## [0.8.0] - 2026-08-19

### Features

- **Project, portfolio and goal tools** — the entities API, distinct from queues and issues ([#45](https://github.com/aikts/yandex-tracker-mcp/pull/45))
  - 39 tools: get/find, create/update/delete with optimistic concurrency via `version`, comments, and checklists (projects and portfolios only — the API has none for goals)
  - Reads take a per-entity `fields` selector defaulting to a small base set, so `metricItems` and a goal's `progressPercentage` / `keyResultItems` must be asked for explicitly
  - Off by default behind `TRACKER_ENTITIES_ENABLED`: they double the tool manifest (43 tools to 82) and are not covered by `TRACKER_LIMIT_QUEUES` / `TRACKER_READ_ONLY_QUEUES`, since an entity has no single queue. `TRACKER_READ_ONLY` still unregisters the write tools
  - `links` are added, never replaced, and are write-only in Tracker: an existing link cannot be re-sent, read back, or removed through this server. A links-only update is rejected rather than reported as a success Tracker silently ignores
  - `*_update_checklist` edits existing items by id; items you don't mention, and fields left unset on ones you do, are left as-is
- **Issue and comment template tools**, read-only ([#43](https://github.com/aikts/yandex-tracker-mcp/issues/43), [#48](https://github.com/aikts/yandex-tracker-mcp/pull/48))
  - `issue_templates_get_all` / `issue_template_get`, `comment_templates_get_all` / `comment_template_get`
  - The issue body a template prefills is in `fieldTemplates.description`, not the template's own `description`
  - Optional `queue` scoping, every page retrieved by default, `TRACKER_LIMIT_QUEUES` enforced
- **`TRACKER_READ_ONLY_QUEUES`** — per-queue read-only access, so one instance can be read-write on some queues and read-only on others ([#36](https://github.com/aikts/yandex-tracker-mcp/issues/36))
- **`TRACKER_API_TIMEOUT`** (default `10`) — the per-request Tracker timeout was hardcoded and could not be raised
- **Paginated listings report their totals.** `issues_find`, `users_get_all`, `queues_get_all` and both template listings answer with `{values, hits, pages}`, built from the `X-Total-Count` / `X-Total-Pages` headers the client used to discard. The last page no longer has to be found by requesting the empty one after it
  - Totals are withheld where they would mislead: on a full walk, and when `TRACKER_LIMIT_QUEUES` hides rows Tracker counted
- **`issues_find` selects fields through the API** (`_search?fields=`), so unwanted fields are never fetched instead of fetched and dropped
  - `fields` now takes any field name, not just the 25 `Issue` declares: `resolution`, `queue`, `project`, `followers`, queue-local and organization-custom fields become selectable. Pass the field `id` from `queue_get_fields`; both `story_points` and `storyPoints` work
- `issue_create` gained the typed reference parameters `issue_update` already had (`parent`, `sprint`, `followers`, `components`, `tags`, `project`, `markup_type`), and `issue_update` gained `assignee` and `components`
- A `fields` map on `issue_create` / `issue_update` overrides the dedicated parameter of the same name, which is how a field is cleared: `{"assignee": null}` clears it
- `get_priorities` returns each priority's `id` and `description`

### Breaking Changes

- Responses use Tracker's own field names instead of the Python ones: `storyPoints`, `createdAt`, `updatedBy`, `textHtml` and the rest. A response can now be fed straight back into a `fields` map; callers reading `story_points` or `created_at` need updating
- `issues_find`, `users_get_all`, `queues_get_all`, `issue_templates_get_all` and `comment_templates_get_all` return `{values, hits, pages}` instead of a bare list — iterate `values`
- `issues_count` returns `{"count": N}` instead of a bare integer, which for a project of 403 issues was indistinguishable from an HTTP 403
- `issue_get_comments` returns the cursor-paginated `{comments, next_cursor}` instead of a list, and without pagination arguments returns the first 50 comments rather than all of them

### Bug Fixes

- `fields` actually filters the response instead of blanking it, in every tool that offers the selector. Asking `issues_find` for `["key"]` used to return a dozen null keys per issue
  - Undeclared fields the API returns (`self`, `id`, `queue`, a queue's `<queue-id>--<key>` local fields) sat in the model's extras, which carry no `exclude_if`, so blanking left them as explicit nulls; they are now dropped
  - `User`, `IssueComment`, `Worklog` and `IssueAttachment` declared optionals with a bare `Field(None)` and leaked nulls the same way. A test now fails if a model reachable from a `fields` selector forgets `exclude_if`
- `issue_create` no longer answers 422 for `components: ["694"]` or `followers: ["8000000000000034"]`: reference values are typed models shared with `issue_update`, with `IssueComponentRef` requiring exactly one of `id` / `name` because Tracker reads a bare string there as a component *name*
- A key in `fields` naming a dedicated parameter no longer fails with `TypeError: got multiple values for keyword argument 'parent'`
- `assignee` and `parent` can be cleared at all — `null` was unreachable and `""` answered 422
- An empty reference object (`type={}`) is refused locally with a readable message instead of an unhelpful 400/422
- API errors carry Tracker's own `errorMessages` / `errors` instead of a bare "Unprocessable Entity"
- A 409 on update raises `IssueVersionConflict`, which explains that queue triggers bump the version right after creation, so the version from `issue_create` must not be reused
- A missing queue raises `QueueNotFound` on every queue-scoped read (`queue_get_tags`, `queue_get_versions`, `queue_get_fields`, `queue_get_metadata`), not just the newest ones
- `queue_get_metadata` returns what `expand` asked for, and answers a requested but empty section with an empty list instead of omitting it
- `IssueComment` is a complete model again: `MaillistReference` was declared after the forward reference that used it, leaving the model unbuilt
- `queue_get_fields` and `get_priorities` are described as what they are, so tool search finds them and callers know `get_global_fields` holds the rest

### Internal

- Entity tool and parameter descriptions state shared rules once in the server instructions instead of repeating them per tool, cutting ~21 KB from the manifest
- Update dependencies: `aiohttp` 3.14.3 (undoing the `<3.14` cap from 0.7.2), `cryptography` 50.0.0, `mcp` 1.29.0, `pydantic-settings` 2.15.0, `yandexcloud` 0.403.0, `yarl` 1.24.5

## [0.7.3] - 2026-07-28

### Bug Fixes
- Constrain the `mcp` SDK dependency to `>=1.21,<2` ([fixes #39](https://github.com/aikts/yandex-tracker-mcp/issues/39))
  - `mcp` 2.0.0 removed `FastMCP` (renamed to `MCPServer`) and dropped the `mcp.server.fastmcp` package, so fresh `uvx`/`pip` installs failed at startup with `ImportError: cannot import name 'FastMCP' from 'mcp.server'`
  - Docker images were unaffected because they build from the pinned `uv.lock`

## [0.7.2] - 2026-06-19

### Features
- Add `issue_get_changelog` MCP tool to read an issue's change history ([#32](https://github.com/aikts/yandex-tracker-mcp/pull/32))
  - Returns status transitions and field edits (who changed what `from` → `to` and when)
  - Also surfaces comment changes and executed triggers in the changelog entries
  - Supports cursor pagination via `cursor`/`next_cursor` and `field`/`type` filters

### Internal
- Clean up `issue_write` elicitation logic
- Update dependencies and downgrade `aiohttp` to 3.13.5

## [0.7.1] - 2026-05-23

### Features
- Add `issue_move` MCP tool to move an issue to a different queue ([#25](https://github.com/aikts/yandex-tracker-mcp/pull/25))
  - Supports `notify`, `notify_author`, `move_all_fields`, and `initial_status` flags
  - Returns the issue with its new key in the target queue
  - When the client supports elicitation, prompts the user to confirm these flags before performing the (irreversible) move; declining or cancelling aborts the move. Clients without elicitation support fall back to the passed-in values
- Add `issue_add_link` and `issue_delete_link` MCP tools to manage links between issues ([fixes #26](https://github.com/aikts/yandex-tracker-mcp/issues/26))
  - `issue_add_link` accepts a `relationship` (e.g. `relates`, `depends on`, `duplicates`) and the target issue key
  - `issue_delete_link` removes a link by its ID
- Add `queue_create_version` MCP tool to create a new version in a queue ([#29](https://github.com/aikts/yandex-tracker-mcp/pull/29))
  - Supports `name`, `description`, `start_date`, and `due_date`
- Support passthrough Bearer OAuth token authentication for reverse proxy / gateway deployments ([#23](https://github.com/aikts/yandex-tracker-mcp/pull/23), [#27](https://github.com/aikts/yandex-tracker-mcp/pull/27))
  - Reads the Yandex OAuth token from the incoming `Authorization: Bearer <token>` header when MCP OAuth middleware does not provide a token

### Bug Fixes
- Ignore unrelated environment variables when loading `Settings` (`extra="ignore"`) ([fixes #22](https://github.com/aikts/yandex-tracker-mcp/issues/22))

## [0.6.3] - 2026-02-08

### Features
- Add `issue_add_comment` MCP tool to add comments to issues with support for summonees, mailing lists, and YFM markup
- Add `issue_update_comment` MCP tool to update existing comments in issues
- Add `issue_delete_comment` MCP tool to delete comments from issues

### Internal
- Update dependencies

## [0.6.2] - 2026-01-30

### Features
- Add `issue_add_worklog` MCP tool to add worklog entries (log spent time) to issues
- Add `issue_update_worklog` MCP tool to update existing worklog entries
- Add `issue_delete_worklog` MCP tool to delete worklog entries from issues

### Internal
- Remove verbose option from pytest configuration

## [0.6.1] - 2026-01-17

### Internal
- Refactor `__main__.py` to extract entry point into a proper `main()` function for better modularity

## [0.6.0] - 2026-01-17

### Breaking Changes
- Redis OAuth store now requires encryption configuration via `OAUTH_ENCRYPTION_KEYS` environment variable
- Existing OAuth tokens stored in Redis without encryption will need to be re-authenticated

### Security
- Add token encryption for Redis OAuth store using Fernet (AES-128)
- Redis keys now use SHA-256 hashes instead of raw tokens to prevent token exposure if Redis is compromised
- Support key rotation with multiple encryption keys (first key encrypts, all keys can decrypt)

### Internal
- Update CI workflow badges in README files to reflect new release workflow
- Consolidate Docker and package workflows into unified release.yml
- Remove Python 3.13t from test matrix

## [0.5.2] - 2026-01-17

### Internal
- Refactor MCP tools into modular structure with separate files by category:
  - `queue.py`: Queue-related tools (read-only)
  - `field.py`: Global field and metadata tools (read-only)
  - `issue_read.py`: Issue read-only tools
  - `issue_write.py`: Issue write tools (conditional on read-only mode)
  - `user.py`: User-related tools (read-only)
- Add comprehensive test suite for TrackerClient and MCP tools
- Delete Smithery support
- Update CLAUDE.md with new project structure documentation

## [0.5.1] - 2026-01-13

### Improvements
- Add MCP server name label to Docker image for better registry discoverability
- Update MCP registry schema to version 2025-12-11
- Add OCI package entry to server.json for Docker image distribution

### Internal
- Fix `ty` command in Taskfile to use `uv run`

## [0.5.0] - 2026-01-12

### Breaking changes

- Tool `queue_get_local_fields` is dropped and replaced with `queue_get_fields` — now this tool combines both regular
  and local queue fields.
- Drop Python 3.10 support, require Python 3.11+

### Features
- Add `issue_update` MCP tool to edit existing issues
  - Supports updating summary, description, parent, sprint, type, priority, followers, project, tags, and custom fields
  - Supports optimistic locking via `version` parameter
- Add `issue_create` MCP tool to create new issues in a queue
  - Supports setting summary, description, type, assignee, priority, and custom fields
- Add `issue_close` MCP tool to close issues with a resolution
  - Automatically finds a transition to 'done' status
- Add `issue_execute_transition` MCP tool to execute status transitions
  - Supports adding comments and setting fields during transition
- Add `issue_get_transitions` MCP tool to get possible status transitions for an issue
- Add `get_resolutions` MCP tool to retrieve all available issue resolutions
- Add `queue_get_metadata` MCP tool to get detailed queue metadata with optional field expansion
  - Supports expanding: `all`, `projects`, `components`, `versions`, `types`, `team`, `workflows`, `fields`, `issueTypesConfig`
- Add `queue_get_fields` MCP tool to retrieve both global and queue-specific local fields
  - Returns combined list of fields with `schema.required` indicating mandatory fields
- Add tool annotations with human-readable titles and `readOnlyHint` flags for MCP tool metadata

### Internal
- Migrate from Makefile to Taskfile for development workflow
- Add Python 3.13t to CI test matrix
- Migrate desktop extension packaging from dxt to mcpb

## [0.4.10] - 2025-12-06

### Bug Fixes
- Make `Status.type` field optional to support custom statuses in Yandex Tracker (fixed by [#10](https://github.com/aikts/yandex-tracker-mcp/pull/10))
  - Custom statuses created by organizations don't have the `type` field assigned
  - The `type` field is only present for standard statuses (new, inProgress, paused, done, cancelled)
  - Fixes validation errors when calling `get_statuses` on organizations with custom statuses

## [0.4.9] - 2025-02-11

### Internal
- Temporarily disable MCP Registry publishing in GitHub Actions workflow
  - Comment out publish step to prevent automatic registry updates
  - Maintain registry login and installation steps for future use

## [0.4.8] - 2025-02-11

### Internal
- Update MCP server schema to version 2025-10-17 in server.json

## [0.4.7] - 2025-02-11

### Features
- Add `fields` parameter to `queues_get_all` tool for selective field inclusion
  - Allows optimizing context window usage by selecting only needed fields (e.g., ["key", "name"])
  - Returns all fields if not specified
- Add pagination support to `queues_get_all` tool
  - New `page` parameter to retrieve specific pages
  - New `per_page` parameter (default: 100)
  - Automatically retrieves all pages if page parameter not specified

### Internal
- Update MCP dependency to version 1.21
- Update Pydantic to version 2.12.4

## [0.4.6] - 2025-10-02

### Improvements
- Add `estimation` and `spent` fields to Issue model for time tracking support
  - `estimation`: Estimated time for the issue (string format)
  - `spent`: Time already spent on the issue (string format)

## [0.4.5] - 2025-09-29

### Features
- Add MCP Registry publishing support in GitHub Actions workflow
  - Automatic publishing to MCP Registry on release
  - GitHub OIDC authentication for registry access
- Add `server.json` for official MCP Registry integration
- Add `mcp-name` identifier to documentation (README.md and README_ru.md)

### Internal
- Update release command documentation to include server.json version checks
- Add MCP Registry token files to .gitignore

## [0.4.4] - 2025-01-14

### Bug Fixes
- Fix Claude Desktop OAuth integration for federative authentication scenarios
  - Make OAuth scopes optional in YandexOAuthAuthorizationServerProvider
  - Add `use_scopes` parameter to control whether OAuth scopes are validated
  - Fix scopes handling to properly support cases where `OAUTH_USE_SCOPES=false`
  - Improve compatibility with Yandex Cloud federative OAuth flows

## [0.4.3] - 2025-09-14

### Features
- Add `users_search` MCP tool for searching users by login, email or real name
  - Uses fuzzy matching with 80% similarity threshold for name searches
  - Prioritizes exact matches for login and email over fuzzy name matches
  - Returns single user, multiple users, or empty list based on search results

### Improvements
- Enhanced Yandex Tracker Query Language documentation with better user field guidance
  - Added instruction to use usernames instead of display names for user fields (Assignee, Author, etc.)
  - Added `me()` function documentation for current user queries
  - Added more examples for user-related queries

### Internal
- Update MCP dependency from version 1.12.3 to 1.14.0 for improved compatibility
- Add thefuzz dependency for fuzzy string matching capabilities

## [0.4.2] - 2025-09-13

### Features
- Add support for Yandex Cloud federative OAuth authentication via OIDC applications
- Enhanced OAuth configuration with new environment variables:
  - `OAUTH_TOKEN_TYPE`: Configure token type (Bearer/OAuth) for federative authentication
  - `OAUTH_USE_SCOPES`: Control whether to use OAuth scopes (required `false` for federation)
- Support for federated accounts authentication through organization identity providers

## [0.4.1] - 2025-01-02

### Features
- Enhanced `issues_find` tool with new `fields` parameter for selective field inclusion to optimize context window usage
- Improved pagination with proper `per_page` parameter and validation

### Improvements
- Code reorganization: moved MCP tools to separate `mcp_tracker/mcp/tools.py` file for better maintainability
- Added MCP resources support with `mcp_tracker/mcp/resources.py` for configuration retrieval
- Enhanced parameter validation with `PageParam` and `PerPageParam` type annotations
- Added `IssueFieldsEnum` for field selection in issue queries
- Updated user configuration keys to snake_case format for consistency

### Internal
- Improved code structure and separation of concerns
- Enhanced type safety with better parameter annotations

## [0.4.0] - 2025-08-01

### Features
- Add multiple authentication methods support:
  - Static IAM token authentication via `TRACKER_IAM_TOKEN` environment variable
  - Dynamic IAM token generation using service account credentials (`TRACKER_SA_KEY_ID`, `TRACKER_SA_SERVICE_ACCOUNT_ID`, `TRACKER_SA_PRIVATE_KEY`)
  - Clear authentication priority order: Dynamic OAuth > Static OAuth > Static IAM > Dynamic IAM
- Update manifest.json and smithery.yaml to support IAM token configuration

### Improvements
- Add custom `IssueNotFound` exception for better error handling
- Change issue-related methods to throw exceptions instead of returning None for 404 responses

### Internal
- Add test infrastructure with pytest configuration and initial test files
- Add test commands to Makefile (`test`, `test-unit`, `test-integration`, `test-cov`)
- Refactor authentication system with multi-tier support in `TrackerClient`

## [0.3.6] - 2025-08-01

### Fixes
- Fix Python library packaging

## [0.3.5] - 2025-07-01

### Features
- Add `get_priorities` MCP tool to retrieve all available issue priorities from Yandex Tracker

### Internal
- Update MCP dependency to version 1.10.0

## [0.3.4] - 2025-07-01

### Features
- Add `issue_get_checklist` MCP tool to retrieve checklist items from Yandex Tracker issues
  - Returns list of checklist items including text, status, assignee, and deadline information
  - Supports all checklist item properties including HTML text rendering and deadline status

### Internal
- Add ChecklistItem and ChecklistItemDeadline Pydantic models for type safety
- Extend IssueProtocol with issue_get_checklist method
- Add caching support for checklist operations

## [0.3.3] - 2025-07-01

### Documentation
- Add Russian README (README_ru.md) with complete translation of all features and setup instructions
- Add Claude Code command files for improved development workflow
- Update README with OAuth read-only configuration (`TRACKER_READ_ONLY` environment variable)
- Minor formatting improvements in documentation

## [0.3.2] - 2025-06-30

### Features
- Add `include_description` parameter to issue tools for better context management
  - `issue_get` tool now accepts optional `include_description` parameter (default: true)
  - `issues_find` tool now accepts optional `include_description` parameter (default: false)
  - Helps optimize token usage by excluding large description fields when not needed

### Internal
- Change BaseTrackerEntity to use `extra="ignore"` by default for better data validation
- Override `extra="allow"` for Issue model specifically to preserve existing API compatibility

## [0.3.1] - 2025-06-30

### Features
- Refactor Yandex OAuth implementation to support dynamic scopes and improve callback handling
- Add usage instructions for Yandex Tracker tools

## [0.3.0] - 2025-06-30

### Features
- Add complete OAuth 2.0 implementation with Yandex integration and protocol refactoring
  - OAuth provider mode for authorization code flow with PKCE support
  - Token management with refresh token support
  - YandexAuth dataclass for authentication encapsulation
  - Optional auth parameter across all protocol methods
- Add user_get_current MCP tool to retrieve current authenticated user information

### Internal
- Update Docker workflow to support manual triggers and branch/tag pushes
- Update CI publish workflow dependencies

## [0.2.20] - 2025-06-29

### Internal
- Version bump only (intermediate release)

## [0.2.19] - 2025-06-27

### Internal
- Enable packagin dxt for all platforms

## [0.2.18] - 2025-06-27

### Internal
- Fix packaging dxt

## [0.2.17] - 2025-06-27

### Internal
- Fix packaging dxt

## [0.2.16] - 2025-06-27

### Internal
- Add dxt logo

## [0.2.15] - 2025-06-27

### Internal
- Add dxt packaging support with GitHub Actions workflow

### Documentation
- Update README.md with Claude Desktop installation instructions

## [0.2.13] - 2025-06-26

### Features
- Add Smithery integration support with dedicated configuration file
- Add configurable `TRACKER_BASE_URL` environment variable for custom API endpoints

### Internal
- Add Dockerfile for Smithery deployment
- Update port configuration to default 8000 across all configs

## [0.2.12] - 2025-06-26

### Features
- Add MCP tool for counting Yandex Tracker issues (`issues_count`)

## [0.2.11] - 2025-06-26

### Internal
- CI changes

## [0.2.10] - 2025-06-26

### Internal
- Remove branch restriction from Docker workflow configuration

## [0.2.9] - 2025-01-26

### Features
- Add MCP tool for retrieving queue versions (`queue_get_versions`)

## [0.2.8] - 2025-01-26

### Features
- Add MCP tool for retrieving single user information (`user_get`)

## [0.2.7] - 2025-01-26

### Features
- Add MCP tool for retrieving user information (`users_get_all`)

### Architecture
- Add `UsersProtocol` interface for user-related operations

### Documentation
- Update CLAUDE.md with BaseTrackerEntity requirement guidelines

## [0.2.6] - 2025-01-26

### Documentation
- Add CHANGELOG.md with complete version history
- Update README.md to document all available MCP tools including `queue_get_tags` and `issue_get_attachments`

## [0.2.5] - 2025-01-24

### Features
- Add MCP tool for retrieving queue tags (`queue_get_tags`)
- Add MCP tool for retrieving issue attachments (`issue_get_attachments`)

## [0.2.4] - 2025-01-24

### Documentation
- Update README with comprehensive MCP client configuration examples
- Add documentation for status and type management functionality

## [0.2.3] - 2025-01-24

### Internal
- Remove yandex-tracker-client dependency from project

## [0.2.2] - 2025-01-23

### Features
- Add MCP tool for retrieving Yandex Tracker issue types (`get_issue_types`)

## [0.2.1] - 2025-01-23

### Features
- Add MCP tool for retrieving statuses (`get_statuses`)
- Add MCP tool for getting global fields from Yandex Tracker (`get_global_fields`)
- Add MCP tool for retrieving queue-specific local fields (`queue_get_local_fields`)
- Enhance issues_find tool with Yandex Tracker Query Language support
- Add support for 'streamable-http' transport option

### Internal
- Rename FieldsProtocol to GlobalDataProtocol
- Add Makefile with development tools and quality checks
- Code cleanup: remove unused imports and reorder import statements

### Documentation
- Add CLAUDE.md for project guidance and development instructions

## [0.1.4] - 2025-01-22

### Internal
- Add mypy configuration for type checking
- Update server.py logic improvements

## [0.1.3] - 2025-01-22

### Documentation
- Add version badge to README

## [0.1.2] - 2025-01-22

### Internal
- Minor version update

## [0.1.1] - 2025-01-22

### Features
- Add executable script entry point for uvx command support

## [0.1.0] - 2025-01-22

### Features
- Initial release
- Core functionality for Yandex Tracker MCP Server
- Support for queues, issues, comments, links, and worklogs
- Redis caching implementation
- Docker support with multi-platform builds (including ARM64)
- Python 3.10+ compatibility

### Internal
- GitHub Actions workflows for testing and PyPI publishing
- Development dependencies for testing and linting

### Documentation
- Comprehensive README documentation
