# Yandex Tracker MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/yandex-tracker-mcp)
![Test Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/test.yml/badge.svg?branch=main)
![Docker Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/docker.yml/badge.svg?branch=main)
![Package Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/package.yml/badge.svg?branch=main)
[![smithery badge](https://smithery.ai/badge/@aikts/yandex-tracker-mcp)](https://smithery.ai/server/@aikts/yandex-tracker-mcp)

A comprehensive Model Context Protocol (MCP) server that enables AI assistants to interact with Yandex Tracker APIs. This server provides secure, authenticated access to Yandex Tracker issues, queues, comments, worklogs, and search functionality with optional Redis caching for improved performance.

<a href="https://glama.ai/mcp/servers/@aikts/yandex-tracker-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@aikts/yandex-tracker-mcp/badge" />
</a>

Documentation in Russian is available [here](README_ru.md) / Документация на русском языке доступна [здесь](README_ru.md).

## Features

- **Complete Queue Management**: List and access all available Yandex Tracker queues with pagination support and tag retrieval
- **User Management**: Retrieve user account information, including login details, email addresses, license status, and organizational data
- **Issue Operations**: Retrieve detailed issue information, comments, related links, worklogs, and attachments
- **Field Management**: Access global fields, queue-specific local fields, statuses, and issue types
- **Advanced Query Language**: Full Yandex Tracker Query Language support with complex filtering, sorting, and date functions
- **Performance Caching**: Optional Redis caching layer for improved response times
- **Security Controls**: Configurable queue access restrictions and secure token handling
- **Multiple Transport Options**: Support for stdio, SSE (deprecated), and HTTP transports for flexible integration
- **OAuth 2.0 Authentication**: Dynamic token-based authentication with automatic refresh support as an alternative to static API tokens
- **Organization Support**: Compatible with both standard and cloud organization IDs

### Organization ID Configuration

Choose one of the following based on your Yandex organization type:

- **Yandex Cloud Organization**: Use `TRACKER_CLOUD_ORG_ID` env var later for Yandex Cloud-managed organizations
- **Yandex 360 Organization**: Use `TRACKER_ORG_ID` env var later for Yandex 360 organizations

You can find your organization ID in the Yandex Tracker URL or organization settings.


## MCP Client Configuration

### Installing extension in Claude Desktop

Yandex Tracker MCP Server can be one-click installed in Claude Desktop as and [extension](https://www.anthropic.com/engineering/desktop-extensions).

#### Prerequisites
There is only one requirement - python 3.12 must be installed on your system.

For macOS users, you can install it using the following command:

```bash
brew install python@3.12
```

#### Installation

1. Download the `*.dxt` file from [GitHub Releases](https://github.com/aikts/yandex-tracker-mcp/releases/latest) for your OS and platform.
2. Double-click the downloaded file to install it in Claude Desktop. ![img.png](images/claude-desktop-install.png)
3. Provide your Yandex Tracker OAuth token when prompted. ![img.png](images/claude-desktop-config.png)
4. Make sure extension is enabled - now you may use this MCP Server.

### Manual installation

#### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed globally
- Valid Yandex Tracker API token with appropriate permissions

The following sections show how to configure the MCP server for different AI clients. You can use either `uvx yandex-tracker-mcp@latest` or the Docker image `ghcr.io/aikts/yandex-tracker-mcp:latest`. Both require these environment variables:

- `TRACKER_TOKEN` - Your Yandex Tracker OAuth token (required)
- `TRACKER_CLOUD_ORG_ID` or `TRACKER_ORG_ID` - Your Yandex Cloud (or Yandex 360) organization ID

<details>
<summary><strong>Claude Desktop</strong></summary>

**Configuration file path:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Using uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "-e", "TRACKER_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

**Using uvx:**
```bash
claude mcp add yandex-tracker uvx yandex-tracker-mcp@latest \
  -e TRACKER_TOKEN=your_tracker_token_here \
  -e TRACKER_CLOUD_ORG_ID=your_cloud_org_id_here \
  -e TRACKER_ORG_ID=your_org_id_here \
  -e TRANSPORT=stdio
```

**Using Docker:**
```bash
claude mcp add yandex-tracker docker "run --rm -i -e TRACKER_TOKEN=your_tracker_token_here -e TRACKER_CLOUD_ORG_ID=your_cloud_org_id_here -e TRACKER_ORG_ID=your_org_id_here -e TRANSPORT=stdio ghcr.io/aikts/yandex-tracker-mcp:latest"
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

**Configuration file path:**
- Project-specific: `.cursor/mcp.json` in your project directory
- Global: `~/.cursor/mcp.json`

**Using uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "-e", "TRACKER_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Windsurf</strong></summary>

**Configuration file path:**
- `~/.codeium/windsurf/mcp_config.json`

Access via: Windsurf Settings → Cascade tab → Model Context Protocol (MCP) Servers → "View raw config"

**Using uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "-e", "TRACKER_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Zed</strong></summary>

**Configuration file path:**
- `~/.config/zed/settings.json`

Access via: `Cmd+,` (macOS) or `Ctrl+,` (Linux/Windows) or command palette: "zed: open settings"

**Note:** Requires Zed Preview version for MCP support.

**Using uvx:**
```json
{
  "context_servers": {
    "yandex-tracker": {
      "source": "custom",
      "command": {
        "path": "uvx",
        "args": ["yandex-tracker-mcp@latest"],
        "env": {
          "TRACKER_TOKEN": "your_tracker_token_here",
          "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
          "TRACKER_ORG_ID": "your_org_id_here"
        }
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "context_servers": {
    "yandex-tracker": {
      "source": "custom",
      "command": {
        "path": "docker",
        "args": [
          "run", "--rm", "-i",
          "-e", "TRACKER_TOKEN",
          "-e", "TRACKER_CLOUD_ORG_ID",
          "-e", "TRACKER_ORG_ID",
          "ghcr.io/aikts/yandex-tracker-mcp:latest"
        ],
        "env": {
          "TRACKER_TOKEN": "your_tracker_token_here",
          "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
          "TRACKER_ORG_ID": "your_org_id_here"
        }
      }
    }
  }
}
```

</details>

<details>
<summary><strong>GitHub Copilot (VS Code)</strong></summary>

**Configuration file path:**
- Workspace: `.vscode/mcp.json` in your project directory
- Global: VS Code `settings.json`

**Option 1: Workspace Configuration (Recommended for security)**

Create `.vscode/mcp.json`:

**Using uvx:**
```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "tracker-token",
      "description": "Yandex Tracker Token",
      "password": true
    },
    {
      "type": "promptString",
      "id": "cloud-org-id",
      "description": "Yandex Cloud Organization ID"
    },
    {
      "type": "promptString",
      "id": "org-id",
      "description": "Yandex Tracker Organization ID (optional)"
    }
  ],
  "servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "${input:tracker-token}",
        "TRACKER_CLOUD_ORG_ID": "${input:cloud-org-id}",
        "TRACKER_ORG_ID": "${input:org-id}",
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "tracker-token",
      "description": "Yandex Tracker Token",
      "password": true
    },
    {
      "type": "promptString",
      "id": "cloud-org-id",
      "description": "Yandex Cloud Organization ID"
    },
    {
      "type": "promptString",
      "id": "org-id",
      "description": "Yandex Tracker Organization ID (optional)"
    }
  ],
  "servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "-e", "TRACKER_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "${input:tracker-token}",
        "TRACKER_CLOUD_ORG_ID": "${input:cloud-org-id}",
        "TRACKER_ORG_ID": "${input:org-id}",
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

**Option 2: Global Configuration**

Add to VS Code `settings.json`:

**Using uvx:**
```json
{
  "github.copilot.chat.mcp.servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "github.copilot.chat.mcp.servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "-e", "TRACKER_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Other MCP-Compatible Clients</strong></summary>

For other MCP-compatible clients, use the standard MCP server configuration format:

**Using uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

**Using Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "-e", "TRACKER_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here",
        "TRACKER_ORG_ID": "your_org_id_here"
      }
    }
  }
}
```

</details>

**Important Notes:**
- Replace placeholder values with your actual credentials
- Restart your AI client after configuration changes
- Ensure `uvx` is installed and available in your system PATH
- For production use, consider using environment variables instead of hardcoding tokens

## Available MCP Tools

The server exposes the following tools through the MCP protocol:

### Queue Management
- **`queues_get_all`**: List all available Yandex Tracker queues
  - Returns paginated queue information
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_local_fields`**: Get local fields for a specific queue
  - Parameters: `queue_id` (string, queue key like "SOMEPROJECT")
  - Returns queue-specific custom fields with id, name, and key
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_tags`**: Get all tags for a specific queue
  - Parameters: `queue_id` (string, queue key like "SOMEPROJECT")
  - Returns list of available tags in the specified queue
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_versions`**: Get all versions for a specific queue
  - Parameters: `queue_id` (string, queue key like "SOMEPROJECT")
  - Returns list of available versions in the specified queue with details like name, description, dates, and status
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

### User Management
- **`users_get_all`**: Get information about user accounts registered in the organization
  - Parameters:
    - `per_page` (optional): Number of users per page (default: 50)
    - `page` (optional): Page number to return (default: 1)
  - Returns paginated list of users with login, email, license status, and organizational details
  - Includes user metadata such as external status, dismissal status, and notification preferences

- **`user_get`**: Get information about a specific user by login or UID
  - Parameters: `user_id` (string, user login like "john.doe" or UID like "12345")
  - Returns detailed user information including login, email, license status, and organizational details
  - Supports both user login names and numeric user IDs for flexible identification

- **`user_get_current`**: Get information about the current authenticated user
  - No parameters required
  - Returns detailed information about the user associated with the current authentication token
  - Includes login, email, display name, and organizational details for the authenticated user

### Field Management
- **`get_global_fields`**: Get all global fields available in Yandex Tracker
  - Returns complete list of global fields that can be used in issues
  - Includes field schema, type information, and configuration

### Status and Type Management
- **`get_statuses`**: Get all available issue statuses
  - Returns complete list of issue statuses that can be assigned
  - Includes status IDs, names, and type information

- **`get_issue_types`**: Get all available issue types
  - Returns complete list of issue types for creating/updating issues
  - Includes type IDs, names, and configuration details

- **`get_priorities`**: Get all available issue priorities
  - Returns complete list of priorities that can be assigned to issues
  - Includes priority keys, names, and order information

### Issue Operations
- **`issue_get`**: Retrieve detailed issue information by ID
  - Parameters:
    - `issue_id` (string, format: "QUEUE-123")
    - `include_description` (boolean, optional, default: true): Whether to include issue description in the result. Can be large, so use only when needed.
  - Returns complete issue data including status, assignee, description, etc.

- **`issue_get_url`**: Generate web URL for an issue
  - Parameters: `issue_id` (string)
  - Returns: `https://tracker.yandex.ru/{issue_id}`

- **`issue_get_comments`**: Fetch all comments for an issue
  - Parameters: `issue_id` (string)
  - Returns chronological list of comments with metadata

- **`issue_get_links`**: Get related issue links
  - Parameters: `issue_id` (string)
  - Returns links to related, blocked, or duplicate issues

- **`issue_get_worklogs`**: Retrieve worklog entries
  - Parameters: `issue_ids` (array of strings)
  - Returns time tracking data for specified issues

- **`issue_get_attachments`**: Get attachments for an issue
  - Parameters: `issue_id` (string, format: "QUEUE-123")
  - Returns list of attachments with metadata for the specified issue

- **`issue_get_checklist`**: Get checklist items of an issue
  - Parameters: `issue_id` (string, format: "QUEUE-123")
  - Returns list of checklist items including text, status, assignee, and deadline information

### Search and Discovery
- **`issues_find`**: Search issues using [Yandex Tracker Query Language](https://yandex.ru/support/tracker/ru/user/query-filter)
  - Parameters:
    - `query` (required): Query string using Yandex Tracker Query Language syntax
    - `include_description` (boolean, optional, default: false): Whether to include issue description in the issues result. Can be large, so use only when needed.
    - `page` (optional): Page number for pagination (default: 1)
  - Returns up to 500 issues per page

- **`issues_count`**: Count issues matching a query using [Yandex Tracker Query Language](https://yandex.ru/support/tracker/ru/user/query-filter)
  - Parameters:
    - `query` (required): Query string using Yandex Tracker Query Language syntax
  - Returns the total count of issues matching the specified criteria
  - Supports all query language features: field filtering, date functions, logical operators, and complex expressions
  - Useful for analytics, reporting, and understanding issue distribution without retrieving full issue data


## http Transport

The MCP server can also be run in streamable-http mode for web-based integrations or when stdio transport is not suitable.

### streamable-http Mode Environment Variables

```env
# Required - Set transport to streamable-http mode
TRANSPORT=streamable-http

# Server Configuration
HOST=0.0.0.0  # Default: 0.0.0.0 (all interfaces)
PORT=8000     # Default: 8000
```

### Starting the streamable-http Server

```bash
# Basic streamable-http server startup
TRANSPORT=streamable-http uvx yandex-tracker-mcp@latest

# With custom host and port
TRANSPORT=streamable-http \
HOST=localhost \
PORT=9000 \
uvx yandex-tracker-mcp@latest

# With all environment variables
TRANSPORT=streamable-http \
HOST=0.0.0.0 \
PORT=8000 \
TRACKER_TOKEN=your_token \
TRACKER_CLOUD_ORG_ID=your_org_id \
uvx yandex-tracker-mcp@latest
```

You may skip configuring `TRACKER_CLOUD_ORG_ID` or `TRACKER_ORG_ID` if you are using the following format when connecting to MCP Server (example for Claude Code):

```bash
claude mcp add --transport http yandex-tracker "http://localhost:8000/mcp/?cloudOrgId=your_cloud_org_id&"
```

or

```bash
claude mcp add --transport http yandex-tracker "http://localhost:8000/mcp/?orgId=org_id&"
```

You may also skip configuring global `TRACKER_TOKEN` environment variable if you choose to use OAuth 2.0 authentication (see below).

### OAuth 2.0 Authentication

The Yandex Tracker MCP Server supports OAuth 2.0 authentication as a secure alternative to static API tokens. When configured, the server acts as an OAuth provider, facilitating authentication between your MCP client and Yandex OAuth services.

#### How OAuth Works

The MCP server implements a standard OAuth 2.0 authorization code flow:

1. **Client Registration**: Your MCP client registers with the server to obtain client credentials
2. **Authorization**: Users are redirected to Yandex OAuth to authenticate
3. **Token Exchange**: The server exchanges authorization codes for access tokens
4. **API Access**: Clients use bearer tokens for all API requests
5. **Token Refresh**: Expired tokens can be refreshed without re-authentication

```
MCP Client → MCP Server → Yandex OAuth → User Authentication
    ↑                                           ↓
    └────────── Access Token ←─────────────────┘
```

#### OAuth Configuration

To enable OAuth authentication, set the following environment variables:

```env
# Enable OAuth mode
OAUTH_ENABLED=true

# Yandex OAuth Application Credentials (required for OAuth)
OAUTH_CLIENT_ID=your_yandex_oauth_app_id
OAUTH_CLIENT_SECRET=your_yandex_oauth_app_secret

# Public URL of your MCP server (required for OAuth callbacks)
MCP_SERVER_PUBLIC_URL=https://your-mcp-server.example.com

# Optional OAuth settings
OAUTH_SERVER_URL=https://oauth.yandex.ru  # Default Yandex OAuth server

# When OAuth is enabled, TRACKER_TOKEN becomes optional
```

#### Setting Up Yandex OAuth Application

1. Go to [Yandex OAuth](https://oauth.yandex.ru/) and create a new application
2. Set the callback URL to: `{MCP_SERVER_PUBLIC_URL}/oauth/yandex/callback`
3. Request the following permissions:
   - `tracker:read` - Read permissions for Tracker
   - `tracker:write` - Write permissions for Tracker
4. Save your Client ID and Client Secret

#### OAuth vs Static Token Authentication

| Feature          | OAuth                          | Static Token               |
|------------------|--------------------------------|----------------------------|
| Security         | Dynamic tokens with expiration | Long-lived static tokens   |
| User Experience  | Interactive login flow         | One-time configuration     |
| Token Management | Automatic refresh              | Manual rotation            |
| Access Control   | Per-user authentication        | Shared token               |
| Setup Complexity | Requires OAuth app setup       | Simple token configuration |

#### OAuth Mode Limitations

- Currently, the OAuth mode requires the MCP server to be publicly accessible for callback URLs
- OAuth mode is best suited for interactive clients that support web-based authentication flows

#### Using OAuth with MCP Clients

When OAuth is enabled, MCP clients will need to:
1. Support OAuth 2.0 authorization code flow
2. Handle token refresh when access tokens expire
3. Store refresh tokens securely for persistent authentication

**Note**: Not all MCP clients currently support OAuth authentication. Check your client's documentation for OAuth compatibility.

Example configuration for Claude Code:

```bash
claude mcp add --transport http yandex-tracker https://your-mcp-server.example.com/mcp/ -s user
```

#### OAuth Data Storage

The MCP server supports two different storage backends for OAuth data (client registrations, access tokens, refresh tokens, and authorization states):

##### InMemory Store (Default)

The in-memory store keeps all OAuth data in server memory. This is the default option and requires no additional configuration.

**Characteristics:**
- **Persistence**: Data is lost when the server restarts
- **Performance**: Very fast access since data is stored in memory
- **Scalability**: Limited to single server instance
- **Setup**: No additional dependencies required
- **Best for**: Development, testing, or single-instance deployments where losing OAuth sessions on restart is acceptable

**Configuration:**
```env
OAUTH_STORE=memory  # Default value, can be omitted
```

##### Redis Store

The Redis store provides persistent storage for OAuth data using a Redis database. This ensures OAuth sessions survive server restarts and enables multi-instance deployments.

**Characteristics:**
- **Persistence**: Data persists across server restarts
- **Performance**: Fast access with network overhead
- **Scalability**: Supports multiple server instances sharing the same Redis database
- **Setup**: Requires Redis server installation and configuration
- **Best for**: Production deployments, high availability setups, or when OAuth sessions must persist

**Configuration:**
```env
# Enable Redis store for OAuth data
OAUTH_STORE=redis

# Redis connection settings (same as used for tools caching)
REDIS_ENDPOINT=localhost                  # Default: localhost
REDIS_PORT=6379                           # Default: 6379
REDIS_DB=0                                # Default: 0
REDIS_PASSWORD=your_redis_password        # Optional: Redis password
REDIS_POOL_MAX_SIZE=10                    # Default: 10
```

**Storage Behavior:**
- **Client Information**: Stored persistently
- **OAuth States**: Stored with TTL (time-to-live) for security
- **Authorization Codes**: Stored with TTL and automatically cleaned up after use
- **Access Tokens**: Stored with automatic expiration based on token lifetime
- **Refresh Tokens**: Stored persistently until revoked
- **Key Namespacing**: Uses `oauth:*` prefixes to avoid conflicts with other Redis data

**Important Notes:**
- Both stores use the same Redis connection settings as the tools caching system
- When using Redis store, ensure your Redis instance is properly secured and accessible
- The `OAUTH_STORE` setting only affects OAuth data storage; tools caching uses `TOOLS_CACHE_ENABLED`
- Redis store uses JSON serialization for better cross-language compatibility and debugging

## Configuration

### Environment Variables

```env
# Required - Yandex Tracker API token
TRACKER_TOKEN=your_yandex_tracker_oauth_token

# Organization Configuration (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id    # For Yandex Cloud organizations
TRACKER_ORG_ID=your_org_id                # For Yandex 360 organizations

# API Configuration (optional)
TRACKER_BASE_URL=https://api.tracker.yandex.net  # Default: https://api.tracker.yandex.net

# Security - Restrict access to specific queues (optional)
TRACKER_LIMIT_QUEUES=PROJ1,PROJ2,DEV      # Comma-separated queue keys

# Server Configuration
HOST=0.0.0.0                              # Default: 0.0.0.0
PORT=8000                                 # Default: 8000
TRANSPORT=stdio                           # Options: stdio, streamable-http, sse

# Redis connection settings (used for caching and OAuth store)
REDIS_ENDPOINT=localhost                  # Default: localhost
REDIS_PORT=6379                           # Default: 6379
REDIS_DB=0                                # Default: 0
REDIS_PASSWORD=your_redis_password        # Optional: Redis password
REDIS_POOL_MAX_SIZE=10                    # Default: 10

# Tools caching configuration (optional)
TOOLS_CACHE_ENABLED=true                  # Default: false
TOOLS_CACHE_REDIS_TTL=3600                # Default: 3600 seconds (1 hour)

# OAuth 2.0 Authentication (optional)
OAUTH_ENABLED=true                        # Default: false
OAUTH_STORE=redis                         # Options: memory, redis (default: memory)
OAUTH_SERVER_URL=https://oauth.yandex.ru  # Default: https://oauth.yandex.ru
OAUTH_CLIENT_ID=your_oauth_client_id      # Required when OAuth enabled
OAUTH_CLIENT_SECRET=your_oauth_secret     # Required when OAuth enabled
MCP_SERVER_PUBLIC_URL=https://your.server.com  # Required when OAuth enabled
TRACKER_READ_ONLY=true                    # Default: false - Limit OAuth to read-only permissions
```

## Docker Deployment

### Using Pre-built Image (Recommended)

```bash
# Using environment file
docker run --env-file .env -p 8000:8000 ghcr.io/aikts/yandex-tracker-mcp:latest

# With inline environment variables
docker run -e TRACKER_TOKEN=your_token \
           -e TRACKER_CLOUD_ORG_ID=your_org_id \
           -p 8000:8000 \
           ghcr.io/aikts/yandex-tracker-mcp:latest
```

### Building the Image Locally

```bash
docker build -t yandex-tracker-mcp .
```

### Docker Compose

**Using pre-built image:**
```yaml
version: '3.8'
services:
  mcp-tracker:
    image: ghcr.io/aikts/yandex-tracker-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - TRACKER_TOKEN=${TRACKER_TOKEN}
      - TRACKER_CLOUD_ORG_ID=${TRACKER_CLOUD_ORG_ID}
```

**Building locally:**
```yaml
version: '3.8'
services:
  mcp-tracker:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TRACKER_TOKEN=${TRACKER_TOKEN}
      - TRACKER_CLOUD_ORG_ID=${TRACKER_CLOUD_ORG_ID}
```

### Development Setup

```bash
# Clone and setup
git clone https://github.com/aikts/yandex-tracker-mcp
cd yandex-tracker-mcp

# Install development dependencies
uv sync --dev

# Formatting and static checking
make
```

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Support

For issues and questions:
- Review Yandex Tracker API documentation
- Submit issues at https://github.com/aikts/yandex-tracker-mcp/issues
