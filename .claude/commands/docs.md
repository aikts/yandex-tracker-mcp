Make sure that @README.md and @AGENTS.md are up to date with current code structure, specification, architecture, features, environment variables. Make sure to also update the translated version at @README_ru.md. Also if there are new tools added to the project - make sure they are documented in @README.md, @README_ru.md, @manifest.json.

Follow @rules/docs.md for how much goes into each of them, and @rules/tool-descriptions.md before touching a tool description. `uv run pytest tests/mcp/server/test_readme_coverage.py tests/mcp/server/test_tool_conventions.py` checks the mechanical part.
