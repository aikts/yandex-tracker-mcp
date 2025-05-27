from mcp_tracker.mcp.server import mcp, settings

if __name__ == "__main__":
    mcp.run(transport=settings.transport)
