"""Tool names and descriptions follow `rules/tool-naming.md` and
`rules/tool-descriptions.md`.

Both rules come from real damage. Descriptions grew into essays a client pays for in
context on every call, and were cut back by hand twice; `issue_get` and `get_priorities`
went the other way and could not be found by tool search at all.
"""

import re

import pytest
from mcp.types import Tool

from tests.mcp.server.test_server_creation import ALL_READ_ONLY_TOOL_NAMES
from tests.mcp.server.tool_listing import REGISTERED_TOOLS, TOOL_NAMES

# Entity prefixes a tool name may start with. A tool for a new entity means adding
# its prefix here, in the same PR - a deliberate line, not a regex that lets
# anything through.
TOOL_NAME_ENTITIES = frozenset(
    {
        "board",
        "boards",
        "comment",
        "goal",
        "issue",
        "issues",
        "portfolio",
        "project",
        "queue",
        "queues",
        "user",
        "users",
    }
)

# Named before the rule existed. A tool name is API - clients call it by name - so
# these stay as they are, and nothing new is named this way.
LEGACY_TOOL_NAMES = frozenset(
    {
        "get_global_fields",
        "get_issue_types",
        "get_priorities",
        "get_resolutions",
        "get_statuses",
    }
)

MIN_DESCRIPTION_LENGTH = 40
MAX_DESCRIPTION_LENGTH = 350

TOOL_NAME_PATTERN = re.compile(r"^([a-z]+)(?:_[a-z0-9]+)+$")

READ_ONLY_NAMES = frozenset(ALL_READ_ONLY_TOOL_NAMES)
NAMED_BY_THE_RULE = [
    tool for tool in REGISTERED_TOOLS if tool.name not in LEGACY_TOOL_NAMES
]


def tool_id(tool: Tool) -> str:
    return tool.name


@pytest.mark.parametrize("tool", NAMED_BY_THE_RULE, ids=tool_id)
def test_tool_is_named_entity_first(tool: Tool) -> None:
    match = TOOL_NAME_PATTERN.match(tool.name)
    assert match is not None, (
        f"'{tool.name}' is not <entity>_<action> - see rules/tool-naming.md"
    )
    assert match.group(1) in TOOL_NAME_ENTITIES, (
        f"'{tool.name}' starts with '{match.group(1)}', which is not a known entity. "
        "Name it after the entity it acts on, or add the entity to TOOL_NAME_ENTITIES."
    )


@pytest.mark.parametrize("name", sorted(LEGACY_TOOL_NAMES))
def test_legacy_names_are_still_registered(name: str) -> None:
    """The exception list may not outlive the tools it excuses."""
    assert name in TOOL_NAMES, (
        f"'{name}' is no longer registered - drop it from LEGACY_TOOL_NAMES"
    )


@pytest.mark.parametrize("tool", REGISTERED_TOOLS, ids=tool_id)
def test_tool_description_fits_the_budget(tool: Tool) -> None:
    description = tool.description or ""

    assert len(description) >= MIN_DESCRIPTION_LENGTH, (
        f"'{tool.name}' has {len(description)} characters of description. Too thin to "
        "rank in tool search - say what it does and what comes back."
    )
    assert len(description) <= MAX_DESCRIPTION_LENGTH, (
        f"'{tool.name}' has {len(description)} characters of description, over the "
        f"{MAX_DESCRIPTION_LENGTH} budget. What a caller acts on stays; the rest goes "
        "to README.md - see rules/tool-descriptions.md."
    )


@pytest.mark.parametrize("tool", REGISTERED_TOOLS, ids=tool_id)
def test_tool_annotates_whether_it_writes(tool: Tool) -> None:
    assert tool.annotations is not None, f"'{tool.name}' declares no ToolAnnotations"
    assert tool.annotations.readOnlyHint is (tool.name in READ_ONLY_NAMES), (
        f"'{tool.name}' has readOnlyHint={tool.annotations.readOnlyHint}, which "
        "contradicts the read-only/write lists in test_server_creation.py"
    )
