# Tool and parameter descriptions

A client pays for every description in context on every call, and tool search ranks on
them. Both failure modes have already happened here: descriptions that grew into essays
("никто в таком объёме читать не будет"), and descriptions so thin that `issue_get` and
`get_priorities` could not be found by search at all.

## Budget

- **One sentence**: what the tool does and what comes back.
- **A second sentence only for a trap** - something that makes the call fail or quietly
  lie, and that the caller cannot see in the schema.
- **Hard bounds: 40-350 characters**, enforced by `tests/mcp/server/test_tool_conventions.py`.
  What does not fit is not important enough for a description; it goes to README.md.

## The first sentence

It is what tool search matches on. It carries the entity noun, the Tracker term, and the
Russian term where the two differ (`'доски'`, `'очередь'`, `'задача'`) - this server is
used against a Russian UI. Where a neighbouring tool is easy to confuse with this one,
name it (`issue_get` reads a known key, `issues_find` searches).

## Never in a description

- **How the tool works inside**: pagination walks, filter strategies, caching, retries.
- **Why it was built that way**, or what it used to do.
- **Parameter names, types and defaults** - the schema carries them, with their own text.
- **The output field by field** - that is the output schema.

## Always in a description, when true

- State that goes stale on its own: `version` after `issue_create`.
- A field that does the opposite of the obvious: `summonees` notifies, an `@login` in the
  comment text notifies nobody.
- What the server itself may refuse: queue allow-lists, read-only mode, an opt-in flag.
- What comes back instead of the obvious thing: "returns the issue's whole checklist".

An API trap belongs in the tool description, not only in AGENTS.md - the agent calling the
tool never reads AGENTS.md.

## Say it once

A fact true of many tools goes into the server instructions in
`mcp_tracker/mcp/server.py`, not into each tool. `tests/mcp/server/test_instructions.py`
fails if those instructions name a tool that is not registered, or promise an argument a
tool does not take.

## Parameters

- A parameter used by two or more tools is an `Annotated` alias in
  `mcp_tracker/mcp/params.py`. **Never copy a `Field(description=...)` between two tools**:
  the `followers` warning about the 422 was pasted into `issue_create` and then lost in
  `issue_update`, and a caller reading only `issue_update` never saw it.
- A create/update pair takes the **same types with the same wording** - AGENTS.md, under
  *Talking to the Tracker API*, says why the types have to match; the wording has to match
  for the same reason.
- A field description says what to pass and what happens when you don't. Not where the
  value comes from inside the server.
