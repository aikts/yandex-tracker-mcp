import sys

from pydantic import ValidationError

from mcp_tracker.mcp.server import create_mcp_server
from mcp_tracker.settings import Settings


def main() -> None:
    """Main entry point for the yandex-tracker-mcp command."""
    try:
        settings = Settings()
    except ValidationError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

    mcp = create_mcp_server(settings)
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
