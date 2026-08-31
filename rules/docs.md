# README.md, README_ru.md, manifest.json

## Coverage

Every registered tool appears in `README.md`, `README_ru.md` and `manifest.json`, and
nothing else does. `tests/mcp/server/test_manifest.py` and
`tests/mcp/server/test_readme_coverage.py` enforce it - which is what would have caught
`get_queue_metadata` and `queue_get_local_fields`, documented for months and never
implemented.

## manifest.json

One sentence per tool: under 160 characters, no markdown, no parameter list. A tool that
needs `TRACKER_ENTITIES_ENABLED` ends its sentence with `(requires TRACKER_ENTITIES_ENABLED)`.

## The tool listing in the READMEs

One table per category, one row per tool:

| Tool | What it does | Key arguments |
| --- | --- | --- |
| `board_get_sprints` | Sprints of a board with status and planned dates | `board_id`, `fields` |

- **The row is one line.** What the caller acts on: what comes back, and the arguments that
  are not self-evident.
- **Traps and constraints that hold for a whole category go under its table**, as at most
  three bullets, once - not repeated per row.
- **No full parameter lists.** The JSON schema already carries types, defaults and
  per-argument text, and a copy in Markdown drifts from it. Spell an argument out only
  where the schema cannot: a format like `QUEUE-123`, or a value that has to come from
  another tool.
- A family of identical tools (`portfolio_*` mirroring `project_*`) still gets its rows -
  a reader looking a tool name up has to find it - but the shared explanation is written
  once, above the table.

## README_ru.md

A translation of README.md, not a superset: same sections, same order, same tables, same
anchors. A fact present in only one of the two is a bug in whichever is missing it.

## Versions

`pyproject.toml`, `manifest.json` and `server.json` (both package versions, and the tag on
the OCI `identifier`) carry the same version, and `CHANGELOG.md` has a section for it.
`tests/test_release_metadata.py` enforces this.
