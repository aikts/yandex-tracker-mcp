"""Both READMEs list exactly the tools the server registers - see `rules/docs.md`.

`get_queue_metadata` and `queue_get_local_fields` were listed for months without ever
existing, and the entity tools were missing in the other direction.
"""

import re
from pathlib import Path

import pytest

from tests.mcp.server.tool_listing import TOOL_NAMES

ROOT = Path(__file__).parents[3]
README_NAMES = ["README.md", "README_ru.md"]
READMES = {name: (ROOT / name).read_text(encoding="utf-8") for name in README_NAMES}

TOOL_CELL_PATTERN = re.compile(r"^`([a-z][a-z0-9_]*)`$")


def listed_tools(readme: str) -> set[str]:
    """The tool names a reader can look up in the READMEs' tool tables.

    A row names its tool in the first cell, and the rest of the row describes it. The
    exception is a table comparing families side by side (`project_*` / `portfolio_*` /
    `goal_*`), whose first cell is prose and whose other cells are the names - so a row
    that does not open with a name contributes every cell that is one.
    """
    listed: set[str] = set()
    for line in readme.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        names = [
            match.group(1) for cell in cells if (match := TOOL_CELL_PATTERN.match(cell))
        ]
        if not names:
            continue
        listed.update(names[:1] if TOOL_CELL_PATTERN.match(cells[0]) else names)

    return listed


LISTED = {name: listed_tools(text) for name, text in READMES.items()}


@pytest.mark.parametrize("readme_name", README_NAMES)
@pytest.mark.parametrize("tool_name", sorted(TOOL_NAMES))
def test_every_tool_is_listed(tool_name: str, readme_name: str) -> None:
    assert tool_name in LISTED[readme_name], (
        f"'{tool_name}' has no row in {readme_name}'s tool tables"
    )


@pytest.mark.parametrize("readme_name", README_NAMES)
def test_no_table_names_a_tool_that_does_not_exist(readme_name: str) -> None:
    unknown = LISTED[readme_name] - TOOL_NAMES

    assert not unknown, (
        f"{readme_name} lists tools this server does not register: {sorted(unknown)}"
    )
