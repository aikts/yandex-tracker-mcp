# Rules

Conventions this repository enforces, split out of [AGENTS.md](../AGENTS.md) because
the same review comments kept coming back: tool descriptions grew into essays nobody
reads, two tools became unfindable by tool search, CHANGELOG entries became unreadable,
and the two READMEs drifted from the code.

| Rule set | Covers |
| --- | --- |
| [tool-naming.md](tool-naming.md) | What a tool is called, and which module it lives in |
| [tool-descriptions.md](tool-descriptions.md) | Tool and parameter descriptions, and where a fact belongs |
| [changelog.md](changelog.md) | `CHANGELOG.md` entries |
| [docs.md](docs.md) | `README.md`, `README_ru.md`, `manifest.json`, version sync |

Every rule that can be checked mechanically has a test, named in the rule. A rule
without a test is still a rule.

AGENTS.md stays the place for architecture and for how the Tracker API behaves.
These files only say what things are called and how much text they get.
