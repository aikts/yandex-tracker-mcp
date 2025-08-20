# Changelog

All notable changes to this project will be documented in this file.

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
