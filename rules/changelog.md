# CHANGELOG

`CHANGELOG.md` is read by someone deciding whether to upgrade, and by an agent asked what
changed. It says **what shipped**, not how it works. Nothing else goes in it.

## Shape

- **Sections in this order**, omitted when empty: `### Features`, `### Bug Fixes`,
  `### Documentation`, `### Internal`.
- **One bullet per change: the substance in one sentence, two at the most.** Lead with the
  subject in bold; link the issue or PR.
- **Sub-bullets are the exception, not the shape.** At most three, and only where a caller
  has to do something differently: a new argument, a changed default, a value no longer
  returned, a flag that gates the tool. Most changes need none and stay one line.
- **`### Internal`: at most two bullets per release.** For a change invisible from the
  outside that a contributor still needs to know (the `_request()` funnel, a dependency
  floor). A bullet that only lists what moved where does not belong - drop it.

## Content

- **Name what changed. Do not explain it.** The mechanics, the counts, the before/after
  detail and the reasoning belong in the commit message and in the code - a reader who
  wants them knows where to look.
- Do not restate the tool description, the README or the rule you just wrote. The name of
  the thing is enough to look it up.
- For a fix, one clause on what was wrong before is worth it. One clause.
- No library internals, no upstream PR archaeology, no file, function or test names.

## The size of an entry

Not this:

> - **`rules/`** - the conventions that kept being re-litigated per change (tool naming,
>   the description budget, CHANGELOG entries, README/manifest coverage), each with the
>   test that enforces it
>   - Six tool descriptions were over the 350-character budget and six under the
>     40-character floor; both ends are now checked, so a description can neither [...]

This:

> - **`rules/`** - guidelines for tool naming, tool and parameter descriptions and the
>   documentation, with the tests that enforce them

## Scope

Entries describe the diff since the previous tag (`git diff <last tag>..HEAD`), **not the
commits in between**. Something introduced and then reworked before the release is one
entry, in its final form; something that only exists on an unreleased branch is not an
entry at all. Getting this wrong once put a `with_board` argument in 0.8.0, for a tool that
did not ship until later.

## Versions

- Every release gets its own section, patch releases included.
- **Never edit a released section.**
- Unreleased work goes under `## [Unreleased]`, and becomes `## [X.Y.Z] - YYYY-MM-DD` at
  release time. `tests/test_release_metadata.py` fails if the version in `pyproject.toml`
  has no section.
