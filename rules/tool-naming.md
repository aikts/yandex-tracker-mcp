# Tool naming

## The pattern

`<entity>_<action>` - the entity first, always.

- **Singular entity** for one record: `issue_get`, `board_get`, `user_get`, `project_update`.
- **Plural entity** for a listing or a search: `issues_find`, `queues_get_all`, `users_search`, `boards_get_all`.
- **A sub-resource keeps the owning entity first**: `issue_get_comments`, `issue_add_checklist_items`, `project_delete_checklist_item` - never `comments_get_for_issue`.
- **Actions, in the spelling already in use**: `get`, `get_all`, `find`, `count`, `create`, `update`, `delete`, `close`, `move`, `add_*`, `move_*`, `execute_*`.

`tests/mcp/server/test_tool_conventions.py` fails on anything else.

## Entities

`board`, `boards`, `comment`, `goal`, `issue`, `issues`, `portfolio`, `project`,
`queue`, `queues`, `user`, `users`.

A tool for a new entity means adding its prefix to `TOOL_NAME_ENTITIES` in that test,
in the same PR - a deliberate line, not a regex that lets anything through.

## Frozen names

`get_global_fields`, `get_statuses`, `get_issue_types`, `get_priorities`,
`get_resolutions` were named before the rule. A tool name is API: clients call it by
name, so these are not renamed. They are listed as exceptions in the test. Do not add
a sixth `get_*` tool by copying their shape.

## Modules

The entity in the name decides the module - `mcp_tracker/mcp/tools/<entity>*.py`, and a
mutating tool goes in `<entity>_write.py`. AGENTS.md has the full table and the flags
that gate each group.
