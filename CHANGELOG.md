# Changelog

All notable changes to this project will be documented in this file.

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
