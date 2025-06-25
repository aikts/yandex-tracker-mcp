from mcp_tracker.mcp.server import mcp, settings


def main() -> None:
    """Main entry point for the yandex-tracker-mcp command."""
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
