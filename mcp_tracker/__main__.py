import sys
from typing import Any

from mcp.server import FastMCP
from pydantic import ValidationError

from mcp_tracker.mcp.server import create_mcp_server
from mcp_tracker.settings import Settings


def create_mcp() -> tuple[FastMCP[Any], Settings]:
    """Main entry point for the yandex-tracker-mcp command."""
    try:
        settings = Settings()
    except ValidationError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

    return create_mcp_server(settings), settings


mcp, settings = create_mcp()


def main() -> None:
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
