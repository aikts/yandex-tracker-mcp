# Yandex Tracker MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/yandex-tracker-mcp)
![Test Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/test.yml/badge.svg?branch=main)
![Release Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/release.yml/badge.svg?branch=main)

mcp-name: io.github.aikts/yandex-tracker-mcp

A comprehensive Model Context Protocol (MCP) server that enables AI assistants to interact with Yandex Tracker APIs. This server provides secure, authenticated access to Yandex Tracker issues, queues, comments, worklogs, and search functionality with optional Redis caching for improved performance.

<a href="https://glama.ai/mcp/servers/@aikts/yandex-tracker-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@aikts/yandex-tracker-mcp/badge" />
</a>

Documentation in Russian is available [here](README_ru.md) / Документация на русском языке доступна [здесь](README_ru.md).

## Features

- **Complete Queue Management**: List and access all available Yandex Tracker queues with pagination support, tag retrieval, and detailed metadata
- **Projects, Portfolios and Goals**: Dedicated read and write tools with explicit schemas for each entity type in the Tracker "entities" API (opt-in via `TRACKER_ENTITIES_ENABLED`)
- **User Management**: Retrieve user account information, including login details, email addresses, license status, and organizational data
- **Full Issue Lifecycle**: Create, read, update, and manage issues with support for custom fields, attachments, and workflow transitions
- **Status Workflow Management**: Execute status transitions, close issues with resolutions, and navigate complex workflows
- **Field Management**: Access global fields, queue-specific local fields, statuses, issue types, priorities, and resolutions
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

#### Installation

1. Download the `*.mcpb` file from [GitHub Releases](https://github.com/aikts/yandex-tracker-mcp/releases/latest).
2. Double-click the downloaded file to install it in Claude Desktop. ![img.png](images/claude-desktop-install.png)
3. Provide your Yandex Tracker OAuth token when prompted. ![img.png](images/claude-desktop-config.png)
4. Make sure extension is enabled - now you may use this MCP Server.

### Manual installation

#### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed globally
- Valid Yandex Tracker API token with appropriate permissions

The following sections show how to configure the MCP server for different AI clients. You can use either `uvx yandex-tracker-mcp@latest` or the Docker image `ghcr.io/aikts/yandex-tracker-mcp:latest`. Both require these environment variables:

- Authentication (one of the following):
  - `TRACKER_TOKEN` - Your Yandex Tracker OAuth token
  - `TRACKER_IAM_TOKEN` - Your IAM token
  - `TRACKER_SA_KEY_ID`, `TRACKER_SA_SERVICE_ACCOUNT_ID`, `TRACKER_SA_PRIVATE_KEY` - Service account credentials
- Organization - exactly one of the following:
  - `TRACKER_CLOUD_ORG_ID` - Your Yandex Cloud organization ID
  - `TRACKER_ORG_ID` - Your Yandex 360 organization ID

> Set **one** of the two. Setting both makes every Tracker call fail with
> `Only one of org_id or cloud_org_id should be provided.` The examples below use
> `TRACKER_CLOUD_ORG_ID`; on Yandex 360, replace that key with `TRACKER_ORG_ID`.

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
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
  -e TRANSPORT=stdio
```

**Using Docker:**
```bash
claude mcp add yandex-tracker docker "run --rm -i -e TRACKER_TOKEN=your_tracker_token_here -e TRACKER_CLOUD_ORG_ID=your_cloud_org_id_here -e TRANSPORT=stdio ghcr.io/aikts/yandex-tracker-mcp:latest"
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
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
          "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
          "ghcr.io/aikts/yandex-tracker-mcp:latest"
        ],
        "env": {
          "TRACKER_TOKEN": "your_tracker_token_here",
          "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "${input:tracker-token}",
        "TRACKER_CLOUD_ORG_ID": "${input:cloud-org-id}",
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
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "your_tracker_token_here",
        "TRACKER_CLOUD_ORG_ID": "your_cloud_org_id_here"
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

<details>
<summary><strong>Queue Management</strong></summary>

- **`queues_get_all`**: List all available Yandex Tracker queues
  - Parameters:
    - `fields` (optional): Fields to include in the response (e.g., ["key", "name"]). Helps optimize context window usage by selecting only needed fields. If not specified, returns all available fields.
    - `page` (optional): Page number to return. If not specified, retrieves all pages automatically.
    - `per_page` (optional): Number of items per page (default: 100)
  - Returns `{values, hits, pages}`. `hits`/`pages` are reported only for an explicit single page on a server without `TRACKER_LIMIT_QUEUES`, since the totals count queues the allow-list then hides
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_tags`**: Get all tags for a specific queue
  - Parameters: `queue_id` (string, queue key like "SOMEPROJECT")
  - Returns list of available tags in the specified queue
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_versions`**: Get all versions for a specific queue
  - Parameters: `queue_id` (string, queue key like "SOMEPROJECT")
  - Returns list of available versions in the specified queue with details like name, description, dates, and status
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_create_version`**: Create a new version in a specific queue
  - Parameters:
    - `queue_id` (string, required): Queue key like "SOMEPROJECT"
    - `name` (string, required): Version name
    - `description` (string, optional): Version description
    - `start_date` (date, optional): Version start date in `YYYY-MM-DD` format
    - `due_date` (date, optional): Version due date in `YYYY-MM-DD` format
  - Returns the created version with details like name, description, dates, and status
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_fields`**: Get fields for a specific queue
  - Parameters:
    - `queue_id` (string, required): Queue key like "SOMEPROJECT"
    - `include_local_fields` (boolean, optional, default: true): Whether to include queue-specific local fields
  - Returns list of global fields and optionally local (queue-specific) fields
  - Makes parallel requests to fetch both field types when `include_local_fields` is true
  - The `schema.required` property indicates whether a field is mandatory
  - Use this to find available and required fields before creating an issue with `issue_create` tool
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`queue_get_metadata`**: Get detailed metadata about a specific queue
  - Parameters:
    - `queue_id` (string, required): Queue key like "SOMEPROJECT"
    - `expand` (array of strings, optional): Fields to expand in the response. Available options: `all`, `projects`, `components`, `versions`, `types`, `team`, `workflows`, `fields`, `issueTypesConfig`
  - Returns queue information including name, description, default type/priority, and optionally expanded data
  - Use `expand: ["issueTypesConfig"]` to get available resolutions for each issue type (needed for `issue_close` tool)
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

</details>

<details>
<summary><strong>Projects, Portfolios and Goals</strong></summary>

Projects, portfolios and goals are separate Yandex Tracker entities (distinct from queues) exposed through the Tracker "entities" API. Each entity type has its own dedicated tool and explicit schema; custom (organization-defined) attributes are not modeled and are not returned.

> **These tools are opt-in.** They are registered only when `TRACKER_ENTITIES_ENABLED=true` (default `false`), because they add a large tool manifest and are not covered by the queue restrictions — see [Queue Access Control](#queue-access-control).

- **`project_get`**: Get a project by its id or shortId
  - Parameters:
    - `entity_id` (string, required): Project id or shortId
    - `fields` (array of strings, optional): Entity fields to include, constrained to the allowed values for this entity type. Defaults to a base field set (`summary`, `description`, `entityStatus`, `start`, `end`, `lead`, `author`, `tags`; goals omit `start`, which the API does not define for them)
  - Returns project metadata (id, shortId, version, createdBy/createdAt/updatedAt) and the requested fields

- **`project_find`**: Search projects by name substring and/or field filters
  - Parameters (all optional): `input` (substring match), `filter` (field criteria map), `order_by`, `order_asc`, `root_only` (exclude nested entities), `page`, `per_page`, `fields`
  - Returns a paginated search result (`hits`, `pages`, `values`)

- **`portfolio_get`** / **`portfolio_find`**: Same shape as `project_get` / `project_find`, for portfolios (a portfolio groups projects and/or other portfolios)

- **`goal_get`** / **`goal_find`**: Same shape as `project_get` / `project_find`, for goals. Goals use a different `entityStatus` value set (`draft`, `according_to_plan`, `at_risk`, `blocked`, `achieved`, `partially_achieved`, `not_achieved`, `exceeded`, `cancelled`)

- **`project_get_comments`**: Get a page of comments of a project by its id or shortId
  - Parameters: `entity_id` (required); `per_page` (optional, default 50); `cursor` (optional, the `next_cursor` from the previous call); `fields` (optional, array of comment field names — text/text_html can be large, so select only what you need; omit to get all fields)
  - Returns `{comments, next_cursor}` (comments have the same shape as issue comments). Cursor-paginated: keep passing `next_cursor` back as `cursor` until it is null
- **`portfolio_get_comments`** / **`goal_get_comments`**: Same shape as `project_get_comments`, for portfolios and goals

Write tools (`project_create`/`project_update`/`project_delete` and the equivalent `portfolio_*` / `goal_*` tools) are also available and are only registered when `TRACKER_ENTITIES_ENABLED` is set and `TRACKER_READ_ONLY` is not:

- **`project_create`**: Create a project. Requires `summary`. Accepts `description`, `lead`, `team_users`, `clients`, `followers`, `start`, `end`, `tags`, `entity_status`, `parent_entity`, `team_access`, and `links`
- **`project_update`**: Update any of the above fields on an existing project. Accepts an optional `comment` and `version` (for optimistic-concurrency conflict detection). Passing `links` **adds** links, it does not replace them — re-sending an existing link fails. Links are write-only in the Tracker API (`links` is not a valid `fields` value and is not returned by get/update), so the current set cannot be read back and links cannot be removed through the server. Tracker also ignores a links-only update, so `links` must accompany a field change or a `comment`; the server rejects a links-only call instead of reporting a no-op as success (all verified against the live API)
- **`project_delete`**: Delete a project. Accepts an optional `with_board` flag to also delete the associated board
- **`portfolio_create`** / **`portfolio_update`** / **`portfolio_delete`**: Same shape as the project write tools
- **`goal_create`** / **`goal_update`** / **`goal_delete`**: Same shape as the portfolio write tools, without `start`, and using the goal `entityStatus` and link-relationship value sets. `goal_delete` has no `with_board` flag, since goals have no board

All create/update tools accept the same `fields` selector as the read tools and return the created/updated entity with those fields populated.

- **`project_add_comment`**: Add a comment to a project. Requires `entity_id` and `text` (Markdown/YFM supported). Accepts optional `summonees` (user logins/IDs to notify — use this instead of `@login` in the text) and `maillist_summonees` (mailing list emails)
- **`project_update_comment`**: Update an existing comment. Requires `entity_id`, `comment_id`, and `text`. Accepts the same optional `summonees` / `maillist_summonees`
- **`project_delete_comment`**: Delete a comment. Requires `entity_id` and `comment_id`
- **`portfolio_add_comment`** / **`portfolio_update_comment`** / **`portfolio_delete_comment`** and **`goal_add_comment`** / **`goal_update_comment`** / **`goal_delete_comment`**: Same shape as the project comment write tools, for portfolios and goals

Projects and portfolios (not goals — the Yandex Tracker API does not support checklists on goals) also expose checklist write tools. All of them return the full updated entity (request `checklistItems` via `fields` to see the current items):

- **`project_add_checklist_item`**: Add a checklist item. Requires `entity_id` and `text`. Accepts optional `checked`, `assignee` (user ID/login), and `deadline` (e.g. `{'date': '2026-08-20T00:00:00.000+0000', 'deadlineType': 'date'}`)
- **`project_update_checklist_item`**: Partially update a checklist item. Requires `entity_id` and `checklist_item_id`; all other fields (`text`, `checked`, `assignee`, `deadline`) are optional and only change what's passed
- **`project_move_checklist_item`**: Reorder a checklist item. Requires `entity_id`, `checklist_item_id`, and `before` (the id of the item to insert immediately above)
- **`project_delete_checklist_item`**: Delete a single checklist item. Requires `entity_id` and `checklist_item_id`
- **`project_update_checklist`**: Edit one or more existing checklist items by id. Requires `entity_id` and `items` (`{id, text, checked?, assignee?, deadline?}` objects). Only the listed items change — the server fetches the current checklist and resends it unmodified for every item you don't mention, working around the API rejecting a partial item list with a 500 (verified against the live API). Use the add/delete item tools to change the set
- **`project_delete_checklist`**: Delete the entire checklist. Requires `entity_id`
- **`portfolio_add_checklist_item`** / **`portfolio_update_checklist_item`** / **`portfolio_move_checklist_item`** / **`portfolio_delete_checklist_item`** / **`portfolio_update_checklist`** / **`portfolio_delete_checklist`**: Same shape as the project checklist write tools, for portfolios

Metrics (`metricItems`, on all three entity types) and a goal's key results (`keyResultItems`) are readable through the `fields` selector — request them explicitly, they are not in the default field set. Writing them is not supported: the API reference doesn't define whether an update replaces or merges these collections.

Not yet supported: writing metrics/key results, and bulk changes — these are tracked for a future iteration.

</details>

<details>
<summary><strong>User Management</strong></summary>

- **`users_get_all`**: Get information about user accounts registered in the organization
  - Parameters:
    - `per_page` (optional): Number of users per page (default: 50)
    - `page` (optional): Page number to return (default: 1)
    - `fields` (array of strings, optional): Fields to include per user. Not specifying this returns all available fields
  - Returns `{values, hits, pages}`: the page of users plus how many users there are in total and how many pages that is
  - Includes user metadata such as external status, dismissal status, and notification preferences
  - The current page is the last one when `page` equals `pages`

- **`user_get`**: Get information about a specific user by login or UID
  - Parameters: `user_id` (string, user login like "john.doe" or UID like "12345")
  - Returns detailed user information including login, email, license status, and organizational details
  - Supports both user login names and numeric user IDs for flexible identification

- **`user_get_current`**: Get information about the current authenticated user
  - No parameters required
  - Returns detailed information about the user associated with the current authentication token
  - Includes login, email, display name, and organizational details for the authenticated user

- **`users_search`**: Search user based on login, email or real name (first or last name, or both)
  - Parameters: `login_or_email_or_name` (string, user login, email or real name to search for)
  - Returns either single user or multiple users if several match the query or an empty list if no users matched
  - Uses fuzzy matching for real names with a similarity threshold of 80%, returning at most the 3 best matches
  - Prioritizes exact matches for login and email over fuzzy name matches

</details>

<details>
<summary><strong>Field Management</strong></summary>

- **`get_global_fields`**: Get all global fields available in Yandex Tracker
  - Returns complete list of global fields that can be used in issues
  - Includes field schema, type information, and configuration

</details>

<details>
<summary><strong>Status and Type Management</strong></summary>

- **`get_statuses`**: Get all available issue statuses
  - Returns complete list of issue statuses that can be assigned
  - Includes status IDs, names, and type information

- **`get_issue_types`**: Get all available issue types
  - Returns complete list of issue types for creating/updating issues
  - Includes type IDs, names, and configuration details

- **`get_priorities`**: Get all available issue priorities
  - Returns complete list of priorities that can be assigned to issues
  - Includes priority keys, names, and order information

- **`get_resolutions`**: Get all available issue resolutions
  - Returns complete list of resolutions that can be used when closing issues
  - Includes resolution keys, names, descriptions, and order information

</details>

<details>
<summary><strong>Templates</strong></summary>

- **`issue_templates_get_all`**: Get all issue templates configured in Yandex Tracker
  - Parameters:
    - `queue` (string, optional): Return only the templates usable in that queue - its own templates plus the ones bound to no queue
    - `page` (integer, optional): Page number, default is all pages
    - `per_page` (integer, optional): Items per page (default: 50)
  - Returns `{values, hits, pages}`; `values` holds the templates teams use for bugs, incidents and other recurring work
  - Includes template id, name, owning queue and the `fieldTemplates` values the template prefills

- **`issue_template_get`**: Get a single issue template by its id
  - Parameters:
    - `template_id` (string): Template identifier, as returned by `issue_templates_get_all`
  - Use this before `issue_create` so the new issue follows the team's current template instead of an invented structure

- **`comment_templates_get_all`**: Get all comment templates configured in Yandex Tracker
  - Parameters:
    - `queue` (string, optional): Return only the templates usable in that queue - its own templates plus the ones bound to no queue
    - `page` (integer, optional): Page number, default is all pages
    - `per_page` (integer, optional): Items per page (default: 50)
  - Returns `{values, hits, pages}`; `values` holds the wording teams reuse when replying on issues
  - Includes template id, name, description, owning queue, the `template` comment text and the `summonees` / `maillistSummonees` such a comment summons

- **`comment_template_get`**: Get a single comment template by its id
  - Parameters:
    - `template_id` (string): Template identifier, as returned by `comment_templates_get_all`
  - Use this before `issue_add_comment` so the comment follows the team's current template

Both listings paginate (the API returns 50 templates per page), so by default they walk every page and return the full set; pass `page` to fetch a single page when the context window is tight. As with `queues_get_all`, `hits`/`pages` are reported only for an explicit single page on a server without `TRACKER_LIMIT_QUEUES`: a full walk already returned everything there is, and the totals count templates the allow-list then hides.

Templates are read-only helpers: the Tracker API has no way to create an issue or a comment *from* a template, so `issue_create` and `issue_add_comment` take no `template_id`. Read the template first and pass its values as the tool's arguments.

All four tools respect `TRACKER_LIMIT_QUEUES`: templates bound to a restricted queue are omitted from the listings and rejected on direct access, while templates without a queue remain visible. Passing a restricted queue as `queue` is rejected as well.

</details>

<details>
<summary><strong>Issue Operations</strong></summary>

- **`issue_get`**: Read one issue (task, ticket, bug) by its key/ID
  - Parameters:
    - `issue_id` (string, format: "QUEUE-123")
    - `include_description` (boolean, optional, default: true): Whether to include issue description in the result. Can be large, so use only when needed.
  - Returns the full issue record: summary, description, status, type, priority, assignee, author, tags, components, sprint, epic, parent, deadline, start date, story points, estimation, spent time, votes, created/updated timestamps and users, the current `version`, and any queue-local or custom fields
  - Call it right before `issue_update` to read a fresh `version` for optimistic locking; use `issues_find` when the key is unknown
  - Comments, links, attachments, worklogs, checklist, changelog and transitions are **not** part of the response - use the dedicated `issue_get_*` tools for those

- **`issue_get_url`**: Generate web URL for an issue
  - Parameters: `issue_id` (string)
  - Returns: `https://tracker.yandex.ru/{issue_id}`

- **`issue_get_comments`**: Fetch a page of comments for an issue
  - Parameters:
    - `issue_id` (string)
    - `per_page` (optional, default 50), `cursor` (optional, the `next_cursor` from the previous call)
    - `fields` (array of strings, optional): Fields to include per comment (text/text_html can be large). Not specifying this returns all available fields
  - Returns `{comments, next_cursor}` — comments in chronological order with metadata. Cursor-paginated: keep passing `next_cursor` back as `cursor` until it is null

- **`issue_add_comment`**: Add a comment to an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `text` (string, required): Comment text (markdown supported by Tracker)
    - `summonees` (array of strings, optional): Users to summon (logins or IDs). **This is the API way to mention/call users** (notifications are triggered by this field, not by `@login` in text).
    - `maillist_summonees` (array of strings, optional): Mailing lists to summon (emails)
    - `markup_type` (string, optional): Use `md` for YFM (markdown)
    - `is_add_to_followers` (boolean, optional, default: true): Add comment author to followers
  - Returns created comment object

- **`issue_update_comment`**: Update an existing comment in an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `comment_id` (int, required): Comment ID
    - `text` (string, required): New comment text (markdown supported by Tracker)
    - `summonees` (array of strings, optional): Users to summon (logins or IDs)
    - `maillist_summonees` (array of strings, optional): Mailing lists to summon (emails)
    - `markup_type` (string, optional): Use `md` for YFM (markdown)
  - Returns updated comment object

- **`issue_delete_comment`**: Delete a comment from an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `comment_id` (int, required): Comment ID
  - Returns: `null` (success)

- **`issue_add_link`**: Create a link between an issue and another issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123"): The current issue
    - `relationship` (string, required): Link type describing how `issue_id` relates to the linked issue. One of: `relates`, `is dependent by`, `depends on`, `is subtask for`, `is parent task for`, `duplicates`, `is duplicated by`, `is epic of`, `has epic`
    - `issue` (string, required): ID or key of the issue to link to (e.g. "TEST-123")
  - Returns created link object

- **`issue_delete_link`**: Delete a link between an issue and another issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `link_id` (int, required): Link ID (as returned by `issue_get_links`)
  - Returns: `null` (success)

- **`issue_get_links`**: Get related issue links
  - Parameters: `issue_id` (string)
  - Returns links to related, blocked, or duplicate issues

- **`issue_get_worklogs`**: Retrieve worklog entries
  - Parameters:
    - `issue_ids` (array of strings)
    - `fields` (array of strings, optional): Fields to include per worklog entry. Not specifying this returns all available fields
  - Returns time tracking data for specified issues

- **`issue_add_worklog`**: Add a worklog entry (log spent time) to an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `duration` (string, required): ISO-8601 duration (e.g. `PT1H30M`)
    - `comment` (string, optional): Worklog comment
    - `start` (datetime, optional): Work start datetime (UTC assumed if timezone is not provided)
  - Returns created worklog entry

- **`issue_update_worklog`**: Update a worklog entry (spent time record) in an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `worklog_id` (int, required): Worklog entry ID
    - `duration` (string, optional): ISO-8601 duration (e.g. `PT1H30M`)
    - `comment` (string, optional): Worklog comment
    - `start` (datetime, optional): Work start datetime (UTC assumed if timezone is not provided)
  - Returns updated worklog entry

- **`issue_delete_worklog`**: Delete a worklog entry (spent time record) from an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `worklog_id` (int, required): Worklog entry ID
  - Returns: `null` (success)

- **`issue_get_attachments`**: Get attachments for an issue
  - Parameters:
    - `issue_id` (string, format: "QUEUE-123")
    - `fields` (array of strings, optional): Fields to include per attachment (the `content` field can be large). Not specifying this returns all available fields
  - Returns list of attachments with metadata for the specified issue

- **`issue_get_checklist`**: Get checklist items of an issue
  - Parameters: `issue_id` (string, format: "QUEUE-123")
  - Returns list of checklist items including text, status, assignee, and deadline information

- **`issue_add_checklist_items`**: Add one or more items to the checklist of an issue (creates the checklist if the issue has none)
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `items` (array, required): Items to append, in order. Each item takes `text` (string, required), `checked` (boolean, optional), `assignee` (login or uid, optional) and `deadline` (object, optional: `{"date": "2026-08-20T00:00:00", "deadline_type": "date"}`)
  - Returns the issue's checklist after the items were added
  - Note: Tracker accepts one item per request, so a batch is sent as one request per item, in the given order

- **`issue_update_checklist_item`**: Update a single checklist item of an issue, e.g. to mark it as checked
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `checklist_item_id` (string, required): Item ID as returned by `issue_get_checklist`
    - `text` (string, optional): New item text; omit to keep the current one
    - `checked` (boolean, optional)
    - `assignee` (string, optional): Login or uid
    - `deadline` (object, optional): `{"date": "2026-08-20T00:00:00", "deadline_type": "date"}`
  - Only the fields you pass are changed; the ones you omit keep their current value
  - Returns the issue's checklist after the change

- **`issue_delete_checklist_item`**: Delete a single item from the checklist of an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123")
    - `checklist_item_id` (string, required): Item ID as returned by `issue_get_checklist`
  - Returns the issue's checklist after the deletion

- **`issue_get_transitions`**: Get possible status transitions for an issue
  - Parameters: `issue_id` (string, format: "QUEUE-123")
  - Returns list of available transitions that can be performed on the issue
  - Each transition includes an ID, display name, and target status information

- **`issue_get_changelog`**: Get the change history (changelog) of an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123"): The issue key
    - `per_page` (integer, optional, default: 50): Number of entries per page
    - `cursor` (string, optional): The `next_cursor` value returned by the previous call; pass it to fetch the next page (cursor pagination)
    - `field` (string, optional): Filter the changelog by a field key (e.g. `status`)
    - `type` (string, optional): Filter by change type (e.g. `IssueWorkflow` for status transitions)
  - Returns an object with `entries` (status transitions and field edits — including who changed what `from` → `to` and when — plus comment changes and executed triggers) and `next_cursor` (pass it back as `cursor` for the next page; `null` when there are no more pages)

- **`issue_execute_transition`**: Execute a status transition for an issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123"): The issue key
    - `transition_id` (string, required): The transition ID to execute. **IMPORTANT**: Must be one of the IDs returned by `issue_get_transitions` tool
    - `comment` (string, optional): Optional comment to add when executing the transition
    - `fields` (object, optional): Dictionary of additional fields to set during the transition. Common fields include `resolution` (e.g., 'fixed', 'wontFix') for closing issues, `assignee` for reassigning, etc.
  - Returns list of available transitions for the new status after the transition is executed
  - **Usage note**: You MUST first call `issue_get_transitions` to retrieve available transitions, then pass one of the returned transition IDs. Do NOT use arbitrary transition IDs.

- **`issue_close`**: Close an issue with a resolution (convenience tool)
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123"): The issue key
    - `resolution_id` (string, required): The resolution ID to set when closing (e.g., 'fixed', 'wontFix', 'duplicate')
    - `comment` (string, optional): Optional comment to add when closing the issue
    - `fields` (object, optional): Dictionary of additional fields to set during the closing transition (e.g. `assignee` for reassigning). Do NOT set `resolution` here - use the dedicated `resolution_id` parameter instead
  - Automatically finds a transition to a 'done' status and executes it with the specified resolution
  - Returns list of available transitions for the new (closed) status
  - **Usage note**: Before closing, you MUST:
    1. Call `issue_get` to retrieve the issue's `type` field
    2. Call `queue_get_metadata` with `expand: ["issueTypesConfig"]` to get available resolutions
    3. Choose a resolution from the `issueTypesConfig` entry matching the issue's type - each issue type has its own set of valid resolutions

- **`issue_create`**: Create a new issue in a queue
  - Parameters:
    - `queue` (string, required): Queue key where to create the issue (e.g., 'MYQUEUE')
    - `summary` (string, required): Issue title/summary
    - `type` (IssueTypeRef or string or int, optional): Issue type with `id` and/or `key`, or the bare key/ID (from `get_issue_types` tool)
    - `description` (string, optional): Issue description (use markdown formatting)
    - `markup_type` (string, optional, default `md`): Markup type for description text (use 'md' for YFM markup)
    - `assignee` (string or int, optional): Assignee login or UID
    - `priority` (IssuePriorityRef or string or int, optional): Priority with `id` and/or `key`, or the bare key/ID (from `get_priorities` tool)
    - `parent` (IssueParentRef or string, optional): Parent issue reference with `id` and/or `key` (e.g., 'QUEUE-123'), or the bare key
    - `sprint` (array of IssueSprintRef, optional): Sprint assignments - array of objects with `id` (int) field
    - `followers` (array of IssueFollowerRef, optional): Followers - array of objects with `id` (user ID/uid or login)
    - `components` (array of IssueComponentRef, optional): Queue components - array of objects with either `id` (numeric component ID) or `name` (component name)
    - `tags` (array of strings, optional): Issue tags
    - `project` (IssueProjectRef, optional): Project with `primary` (int, main project shortId) and optional `secondary` (array of ints)
    - `fields` (object, optional): Additional fields without a dedicated parameter. **IMPORTANT**: Before creating an issue, you MUST call `queue_get_fields` to get available fields (it returns both global and local fields by default). Fields with `schema.required=true` are mandatory. Use the field's `id` property as the key in this map (e.g., `{"fieldId": "value"}`). Values are passed to Tracker as-is
  - Returns the newly created issue object with all standard issue fields
  - Accepts the same value formats as `issue_update`, so a reference value that works there works here too
  - **Version note**: the returned `version` can already be outdated - queue triggers and automation run right after creation and bump it. Do not feed it into a follow-up `issue_update`; re-read the issue with `issue_get` or omit `version`
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`issue_update`**: Update an existing issue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123"): The issue key to update
    - `summary` (string, optional): New issue title/summary
    - `description` (string, optional): New issue description
    - `markup_type` (string, optional): Markup type for description text (use 'md' for YFM markup)
    - `parent` (IssueParentRef or string, optional): Parent issue reference with `id` (string) and/or `key` (string, e.g., 'QUEUE-123'), or the bare key
    - `sprint` (array of IssueSprintRef, optional): Sprint assignments - array of objects with `id` (int) field
    - `type` (IssueTypeRef or string or int, optional): Issue type with `id` (string) and/or `key` (string, e.g., 'bug', 'task'), or the bare key/ID
    - `priority` (IssuePriorityRef or string or int, optional): Priority with `id` (string) and/or `key` (string, e.g., 'critical', 'normal'), or the bare key/ID
    - `assignee` (string or int, optional): New assignee login or UID
    - `followers` (array of IssueFollowerRef, optional): Followers - array of objects with `id` (user ID/uid or login); replaces the current list
    - `components` (array of IssueComponentRef, optional): Queue components - array of objects with either `id` (numeric component ID) or `name` (component name); replaces the current list
    - `project` (IssueProjectRef, optional): Project with `primary` (int, main project shortId) and optional `secondary` (array of ints)
    - `tags` (array of strings, optional): Issue tags
    - `version` (int, optional): Issue version for optimistic locking - changes are only applied when it is the issue's current version
    - `fields` (object, optional): Additional fields without a dedicated parameter. Use `queue_get_fields` to discover available fields. Values are passed to Tracker as-is
  - Returns the updated issue object with all standard issue fields
  - Only provided fields are updated; omitted fields remain unchanged
  - **Version note**: read `version` with `issue_get` immediately before updating, or omit it to update whatever the latest version is. A stale version fails with an editing conflict, which is easy to hit with the version returned by `issue_create` because queue triggers bump it
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

- **`issue_move`**: Move an issue to a different queue
  - Parameters:
    - `issue_id` (string, required, format: "QUEUE-123"): The issue key to move
    - `queue` (string, required): Target queue key (e.g., 'MYQUEUE')
    - `notify` (boolean, optional, default `true`): Notify users referenced in the issue's fields
    - `notify_author` (boolean, optional, default `false`): Notify the issue author
    - `move_all_fields` (boolean, optional, default `false`): Carry over versions, components and projects when matching ones exist in the target queue; otherwise they are cleared
    - `initial_status` (boolean, optional, default `false`): Reset the issue status to the initial value (use when the target queue has a different workflow)
  - Returns the updated issue object with its new key in the target queue (e.g., `TASKS-1` → `NEWQUEUE-42`)
  - When the MCP client supports elicitation, the user is prompted to confirm the boolean flags before the move is performed; declining or cancelling aborts the move. Clients without elicitation support proceed with the passed-in values
  - Respects `TRACKER_LIMIT_QUEUES` restrictions

</details>

<details>
<summary><strong>Search and Discovery</strong></summary>

- **`issues_find`**: Search issues using [Yandex Tracker Query Language](https://yandex.ru/support/tracker/ru/user/query-filter)
  - Parameters:
    - `query` (required): Query string using Yandex Tracker Query Language syntax
    - `include_description` (boolean, optional, default: false): Whether to include issue description in the issues result. Can be large, so use only when needed. Ignored when `description` is listed in `fields` - naming it there is an explicit request for it.
    - `fields` (list of strings, optional): Fields to return, in Tracker's own spelling (`storyPoints`, not `story_points`). Any field name is accepted, including a queue's local and the organization's custom fields - pass the field `id` from `queue_get_fields`. A name Tracker does not know is dropped silently. If not specified, returns all available fields.
    - `page` (optional): Page number for pagination (default: 1)
    - `per_page` (optional): Number of items per page (default: 100). May be decreased if results exceed context window.
  - Returns `{values, hits, pages}`: the page of issues plus how many issues match in total and how many pages that is

- **`issues_count`**: Count issues matching a query using [Yandex Tracker Query Language](https://yandex.ru/support/tracker/ru/user/query-filter)
  - Parameters:
    - `query` (required): Query string using Yandex Tracker Query Language syntax
  - Returns `{"count": N}` - the number of issues matching the specified criteria
  - Supports all query language features: field filtering, date functions, logical operators, and complex expressions
  - Useful for analytics, reporting, and understanding issue distribution without retrieving full issue data

</details>

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

##### OAuth Scopes

With `OAUTH_USE_SCOPES=true` (the default) the server requests, advertises and requires the Yandex
Tracker scopes `tracker:read` and `tracker:write` - or `tracker:read` alone when
`TRACKER_READ_ONLY=true`, so a read-only instance never asks the user for write access. Setting
`OAUTH_USE_SCOPES=false` drops scopes from the flow entirely, which is what Yandex Cloud federation
requires.

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

##### Token Encryption (Required for Redis Store)

When using Redis store, you must configure encryption to protect OAuth tokens at rest. Token values are encrypted using Fernet (AES-128) and Redis keys use SHA-256 hashes instead of raw tokens, preventing token exposure if Redis is compromised.

**Generate an encryption key:**
```bash
python3 -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

**Configuration:**
```env
# Single encryption key
OAUTH_ENCRYPTION_KEYS=<base64-encoded-32-byte-key>

# Multiple keys for rotation (first encrypts, all decrypt)
OAUTH_ENCRYPTION_KEYS=<new-key>,<old-key>
```

Key rotation allows seamless key updates: add the new key first, wait for old tokens to expire, then remove the old key.

**Important Notes:**
- Both stores use the same Redis connection settings as the tools caching system
- When using Redis store, ensure your Redis instance is properly secured and accessible
- The `OAUTH_STORE` setting only affects OAuth data storage; tools caching uses `TOOLS_CACHE_ENABLED`
- Redis store uses JSON serialization for better cross-language compatibility and debugging

## Authentication

Yandex Tracker MCP Server supports multiple authentication methods with a clear priority order. The server will use the first available authentication method based on this hierarchy:

### Authentication Priority Order

1. **Dynamic OAuth Token** (highest priority)
   - When OAuth is enabled and a user authenticates via OAuth flow
   - Tokens are dynamically obtained and refreshed per user session
   - Supports both standard Yandex OAuth and Yandex Cloud federative OAuth
   - Required env vars: `OAUTH_ENABLED=true`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `MCP_SERVER_PUBLIC_URL`
   - Additional vars for federative OAuth: `OAUTH_SERVER_URL=https://auth.yandex.cloud/oauth`, `OAUTH_TOKEN_TYPE=Bearer`, `OAUTH_USE_SCOPES=false`

2. **Passthrough Bearer OAuth Token**
   - When MCP OAuth middleware does not provide a token, the server can read a Yandex OAuth token from the incoming `Authorization: Bearer <token>` header
   - Useful behind a trusted reverse proxy or gateway that authenticates users, resolves their stored Yandex OAuth token, and injects it per request
   - The token from MCP OAuth still has priority when OAuth mode is enabled and active

3. **Static OAuth Token**
   - Traditional OAuth token provided via environment variable
   - Single token used for all requests
   - Required env var: `TRACKER_TOKEN` (your OAuth token)

4. **Static IAM Token**
   - IAM (Identity and Access Management) token for service-to-service authentication
   - Suitable for automated systems and CI/CD pipelines
   - Required env var: `TRACKER_IAM_TOKEN` (your IAM token)

5. **Dynamic IAM Token** (lowest priority)
   - Automatically retrieved using service account credentials
   - Token is fetched and refreshed automatically
   - Required env vars: `TRACKER_SA_KEY_ID`, `TRACKER_SA_SERVICE_ACCOUNT_ID`, `TRACKER_SA_PRIVATE_KEY`

### Authentication Scenarios

#### Scenario 1: OAuth with Dynamic Tokens (Recommended for Interactive Use)
```env
# Enable OAuth mode
OAUTH_ENABLED=true
OAUTH_CLIENT_ID=your_oauth_app_id
OAUTH_CLIENT_SECRET=your_oauth_app_secret
MCP_SERVER_PUBLIC_URL=https://your-server.com

# Organization ID (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id  # or TRACKER_ORG_ID
```

#### Scenario 2: Static OAuth Token (Simple Setup)
```env
# OAuth token
TRACKER_TOKEN=your_oauth_token

# Organization ID (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id  # or TRACKER_ORG_ID
```

#### Scenario 3: Passthrough Bearer Token Behind a Reverse Proxy
Use this mode when a trusted gateway handles user authentication, looks up the user's Yandex OAuth token, and forwards the request to the MCP server with that token in the request header:

```http
Authorization: Bearer <user_yandex_oauth_token>
```

```env
# Organization ID (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id  # or TRACKER_ORG_ID
```

This passthrough token is used only when MCP OAuth middleware has not provided an access token for the request. In OAuth-enabled deployments with an active MCP OAuth session, the MCP OAuth token takes priority.

#### Scenario 4: Static IAM Token
```env
# IAM token
TRACKER_IAM_TOKEN=your_iam_token

# Organization ID (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id  # or TRACKER_ORG_ID
```

#### Scenario 5: Dynamic IAM Token with Service Account
```env
# Service account credentials
TRACKER_SA_KEY_ID=your_key_id
TRACKER_SA_SERVICE_ACCOUNT_ID=your_service_account_id
TRACKER_SA_PRIVATE_KEY=your_private_key

# Organization ID (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id  # or TRACKER_ORG_ID
```

#### Scenario 6: Federative OAuth for OIDC Applications (Advanced)
```env
# Enable OAuth with Yandex Cloud federation
OAUTH_ENABLED=true
OAUTH_SERVER_URL=https://auth.yandex.cloud/oauth
OAUTH_TOKEN_TYPE=Bearer
OAUTH_USE_SCOPES=false
OAUTH_CLIENT_ID=your_oidc_client_id
OAUTH_CLIENT_SECRET=your_oidc_client_secret
MCP_SERVER_PUBLIC_URL=https://your-server.com

# Organization ID (choose one)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id  # or TRACKER_ORG_ID
```

This configuration enables authentication through [Yandex Cloud OIDC applications](https://yandex.cloud/ru/docs/organization/operations/applications/oidc-create), which is required for [federated accounts](https://yandex.cloud/ru/docs/organization/operations/manage-federations) in Yandex Cloud. Federated users authenticate through their organization's identity provider (IdP) and use this OAuth flow to access Yandex Tracker APIs.

### Important Notes

- The server checks authentication methods in the order listed above
- Only one authentication method will be used at a time
- For production use, dynamic tokens (OAuth or IAM) are recommended for better security
- IAM tokens have a shorter lifetime than OAuth tokens and may need more frequent renewal
- When using service accounts, ensure the account has appropriate permissions for Yandex Tracker

## Configuration

### Environment Variables

```env
# Authentication (use one of the following methods)
# Method 1: OAuth Token
TRACKER_TOKEN=your_yandex_tracker_oauth_token

# Method 2: IAM Token
TRACKER_IAM_TOKEN=your_iam_token

# Method 3: Service Account (for dynamic IAM token)
TRACKER_SA_KEY_ID=your_key_id                    # Service account key ID
TRACKER_SA_SERVICE_ACCOUNT_ID=your_sa_id        # Service account ID
TRACKER_SA_PRIVATE_KEY=your_private_key          # Service account private key

# Organization Configuration (set exactly one - setting both is an error)
TRACKER_CLOUD_ORG_ID=your_cloud_org_id    # For Yandex Cloud organizations
TRACKER_ORG_ID=your_org_id                # For Yandex 360 organizations

# API Configuration (optional)
TRACKER_API_BASE_URL=https://api.tracker.yandex.net  # Default: https://api.tracker.yandex.net
TRACKER_API_TIMEOUT=10                    # Default: 10 - Per-request timeout in seconds for Tracker API calls

# Security - Restrict access to specific queues (optional)
TRACKER_LIMIT_QUEUES=PROJ1,PROJ2,DEV      # Comma-separated queue keys - allow-list of accessible queues
TRACKER_READ_ONLY_QUEUES=PROJ2            # Comma-separated queue keys - allowed for reads but reject writes (per-queue read-only)
TRACKER_ENTITIES_ENABLED=true             # Default: false - Register project/portfolio/goal tools (NOT covered by the queue restrictions above)

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
OAUTH_SERVER_URL=https://oauth.yandex.ru  # Default: https://oauth.yandex.ru (use https://auth.yandex.cloud/oauth for federation)
OAUTH_TOKEN_TYPE=<Bearer|OAuth|<empty>>   # Default: <empty> (required to be Bearer for Yandex Cloud federation)
OAUTH_USE_SCOPES=true                     # Default: true (set to false for Yandex Cloud federation)
OAUTH_CLIENT_ID=your_oauth_client_id      # Required when OAuth enabled
OAUTH_CLIENT_SECRET=your_oauth_secret     # Required when OAuth enabled
MCP_SERVER_PUBLIC_URL=https://your.server.com  # Required when OAuth enabled
TRACKER_READ_ONLY=true                    # Default: false - Disable all write tools for the whole instance
```

### Queue Access Control

Access to queues can be scoped at three levels, from coarse to fine-grained:

- **`TRACKER_LIMIT_QUEUES`** — allow-list of queue keys. Queues outside the list
  are treated as *not found / not allowed* for both reads and writes.
- **`TRACKER_READ_ONLY`** — when `true`, all write tools are unregistered, so the
  whole instance is read-only.
- **`TRACKER_READ_ONLY_QUEUES`** — per-queue read-only allow-list. Write tools stay
  registered, but any mutating call (create/update/move/comment/worklog/link,
  queue version creation) targeting a listed queue is rejected, while reads keep
  working. Queues not listed here remain read-write.

> **Project/portfolio/goal tools are outside this model.** A project, portfolio or
> goal isn't reliably mappable to a single queue, so none of the three settings
> above constrain them — neither the read tools (`project_get`, `project_find`,
> `*_get_comments`, …) nor the write tools (including comment and checklist
> tools). Enabling them grants org-wide access to those entities for anyone who
> can reach the server. For this reason they are **opt-in**: they are registered
> only when `TRACKER_ENTITIES_ENABLED=true` (default `false`), which also keeps
> the tool manifest small for deployments that don't need them. `TRACKER_READ_ONLY`
> still applies: it unregisters entity write tools along with all other write tools.

This lets a single instance be **read-write on some queues and read-only on
others** at the same time — e.g. `TRACKER_LIMIT_QUEUES=DEV,MGMT` together with
`TRACKER_READ_ONLY_QUEUES=MGMT` gives full access to `DEV` and read-only
visibility into `MGMT`. This is especially useful for a shared MCP gateway where
end users reach Tracker only through the server and never hold the raw token
themselves.

> These checks are in-process guardrails. For clients that hold the raw Tracker
> token directly, real limits should additionally be enforced on the token itself.

## Docker Deployment

### Using Pre-built Image (Recommended)

The image defaults to `TRANSPORT=stdio`, which talks over the container's stdin/stdout and
opens no port. Set `TRANSPORT=streamable-http` for the examples below, where the server is
reached over HTTP; for a stdio client, run the container with `-i` and no `-p` instead (see
the [MCP Client Configuration](#mcp-client-configuration) examples).

```bash
# Using environment file (it must set TRANSPORT=streamable-http)
docker run --env-file .env -p 8000:8000 ghcr.io/aikts/yandex-tracker-mcp:latest

# With inline environment variables
docker run -e TRACKER_TOKEN=your_token \
           -e TRACKER_CLOUD_ORG_ID=your_org_id \
           -e TRANSPORT=streamable-http \
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
services:
  mcp-tracker:
    image: ghcr.io/aikts/yandex-tracker-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - TRACKER_TOKEN=${TRACKER_TOKEN}
      - TRACKER_CLOUD_ORG_ID=${TRACKER_CLOUD_ORG_ID}
      - TRANSPORT=streamable-http
```

**Building locally:**
```yaml
services:
  mcp-tracker:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TRACKER_TOKEN=${TRACKER_TOKEN}
      - TRACKER_CLOUD_ORG_ID=${TRACKER_CLOUD_ORG_ID}
      - TRANSPORT=streamable-http
```

### Development Setup

```bash
# Clone and setup
git clone https://github.com/aikts/yandex-tracker-mcp
cd yandex-tracker-mcp

# Install development dependencies
uv sync --dev

# Formatting and static checking
task
```

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Support

For issues and questions:
- Review Yandex Tracker API documentation
- Submit issues at https://github.com/aikts/yandex-tracker-mcp/issues
