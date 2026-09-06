from mcp.server.mcpserver.exceptions import ToolError


class TrackerError(ToolError):
    """Base class for all tracker-related exceptions.

    Subclasses `ToolError` so the message reaches the model: the SDK forwards a
    `ToolError`'s text in the tool result and hides the text of any other
    exception behind a bare `Error executing tool <name>`.
    """

    pass
