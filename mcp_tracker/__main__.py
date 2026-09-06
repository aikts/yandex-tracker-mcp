import sys

from mcp.server.mcpserver import MCPServer
from pydantic import ValidationError

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.server import create_mcp_server
from mcp_tracker.settings import Settings


def create_mcp() -> tuple[MCPServer[AppContext], Settings]:
    """Main entry point for the yandex-tracker-mcp command."""
    try:
        settings = Settings()
    except ValidationError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)

    return create_mcp_server(settings), settings


mcp, settings = create_mcp()


def main() -> None:
    # `run()` is overloaded per transport: an option the transport does not
    # take (e.g. `host` on stdio) is a TypeError, so dispatch explicitly.
    match settings.transport:
        case "stdio":
            mcp.run(transport="stdio")
        case "sse":
            mcp.run(transport="sse", host=settings.host, port=settings.port)
        case "streamable-http":
            mcp.run(
                transport="streamable-http",
                host=settings.host,
                port=settings.port,
                stateless_http=True,
                json_response=True,
            )


if __name__ == "__main__":
    main()
