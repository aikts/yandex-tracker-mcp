"""Board and sprint MCP tools (read-only)."""

from typing import Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import BoardID, PageParam, PerPageParam
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.boards import Board, Sprint


def register_board_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register board and sprint tools (all read-only)."""

    @mcp.tool(
        title="Get All Boards",
        description="Get the agile boards (in russian - 'доски') available in Yandex Tracker. "
        "Use the returned board id with the `board_get_sprints` tool to look up sprints of a board. "
        "An organization can have hundreds of boards, so the listing is paginated - "
        "keep increasing `page` until it comes back empty.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def boards_get_all(
        ctx: Context[Any, AppContext],
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> list[Board]:
        boards = await ctx.request_context.lifespan_context.boards.boards_list(
            auth=get_yandex_auth(ctx),
        )
        # `GET /v3/boards` ignores `page` / `perPage` and always answers with every
        # board, so the paging has to happen here. Left unbounded the tool returns
        # a quarter of a megabyte of JSON on a real organization, which is enough
        # to exhaust the caller's context on a single call.
        start = (page - 1) * per_page
        return boards[start : start + per_page]

    @mcp.tool(
        title="Get Board Sprints",
        description="Get all sprints (in russian - 'спринты') of a specific Yandex Tracker agile board. "
        "The currently running sprint is the one with status 'in_progress'. "
        "Use the returned sprint id to put an issue into a sprint "
        "with the `issue_create` or `issue_update` tools.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def board_get_sprints(
        ctx: Context[Any, AppContext],
        board_id: BoardID,
    ) -> list[Sprint]:
        return await ctx.request_context.lifespan_context.boards.board_get_sprints(
            board_id,
            auth=get_yandex_auth(ctx),
        )
