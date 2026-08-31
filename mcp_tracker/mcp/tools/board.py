"""Board and sprint MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    BoardCursorParam,
    BoardID,
    BoardQueueFilter,
    CursorPerPageParam,
)
from mcp_tracker.mcp.tools._access import check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.boards import (
    Board,
    BoardColumnDetail,
    BoardFieldsEnum,
    BoardsPage,
    Sprint,
    SprintFieldsEnum,
)

# Page size for the walk `queue` needs. On a real organization's 415 boards,
# 25 / 50 / 100 per page cost about the same in total, so take the fewest round
# trips: 100.
BOARDS_SCAN_PAGE = 100

BoardFieldsParam = Annotated[
    list[BoardFieldsEnum] | None,
    Field(
        description="Fields to include in the response; omit to get all. id and name "
        "are usually enough while searching - read the one board you need in full with "
        "`board_get`.",
    ),
]

SprintFieldsParam = Annotated[
    list[SprintFieldsEnum] | None,
    Field(
        description="Fields to include in the response; omit to get all. id, name and "
        "status are usually enough.",
    ),
]


def board_queue_keys(board: Board) -> set[str]:
    """Queue keys a board collects issues from, read off its own auto-filter.

    A board carries no queue field: what lands on it is whatever
    `addFilterSettings` matches. An inverted condition ("queue is not X") says
    which queue the board is *not* about, so it is not a match.
    """
    settings = board.autoFilterSettings
    add = settings.addFilterSettings if settings is not None else None
    live = add.liveFilter if add is not None else None
    if live is None or live.fieldValues is None:
        return set()

    keys: set[str] = set()
    for field in live.fieldValues:
        # The captured payloads name this field twice, `id` and `key`, so
        # matching on both keeps this working whichever one a response carries.
        if "queue" not in (field.id, field.key) or field.value is None:
            continue
        for value in field.value:
            fixed = value.fixed
            if value.invert or fixed is None or isinstance(fixed, str):
                continue
            if fixed.key is not None:
                keys.add(fixed.key.upper())

    return keys


def register_board_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register board and sprint tools (all read-only)."""

    @mcp.tool(
        title="Get All Boards",
        description="Get the agile boards (in russian - 'доски') of the organization; "
        "pass `queue` for the boards collecting issues of that queue. Matching is done "
        "on the board's own filter, so boards filtering by something else are missed - "
        "read a few issues with `issues_find` and look at their `boards` field for "
        "those.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def boards_get_all(
        ctx: Context[Any, AppContext],
        queue: BoardQueueFilter = None,
        fields: BoardFieldsParam = None,
        cursor: BoardCursorParam = None,
        per_page: CursorPerPageParam = 25,
    ) -> BoardsPage:
        if queue is not None:
            check_queue_access(settings, queue)

        boards_api = ctx.request_context.lifespan_context.boards
        auth = get_yandex_auth(ctx)

        if queue is None:
            boards = await boards_api.boards_list(
                per_page=per_page, cursor=cursor, auth=auth
            )
            # `_paginate` sorts by id ascending, so the id of the last board is
            # the cursor for the next page; a short page means there is none.
            next_cursor = boards[-1].id if len(boards) == per_page and boards else None
        else:
            # No server-side filter here - a board is matched by the queue in
            # its own auto-filter - so the listing has to be walked. A page at a
            # time, not the unpaged endpoint: that request grows without bound,
            # and no timeout covers both a small Tracker and a large one.
            # `board_queue_keys` upper-cases what it reads, so the match ignores
            # case the way the allow-list check does.
            wanted = queue.upper()
            boards = []
            next_cursor = cursor
            while len(boards) < per_page:
                batch = await boards_api.boards_list(
                    per_page=BOARDS_SCAN_PAGE, cursor=next_cursor, auth=auth
                )
                boards.extend(b for b in batch if wanted in board_queue_keys(b))
                if len(batch) < BOARDS_SCAN_PAGE:
                    # Short page: the listing is exhausted, so there is nothing
                    # left to continue from however few matches were found.
                    next_cursor = None
                    break
                # The cursor follows the boards examined, not the ones matched,
                # or continuing would rescan everything between two matches.
                next_cursor = batch[-1].id

        if fields is not None:
            set_non_needed_fields_null(boards, {f.name for f in fields})

        return BoardsPage(boards=boards, next_cursor=next_cursor)

    @mcp.tool(
        title="Get Board",
        description="Get a single Yandex Tracker agile board (in russian - 'доска') "
        "with its settings, columns, the field issues are estimated by and the working "
        "calendar. `autoFilterSettings` is the board's own filter and tells which "
        "issues it collects - read it to learn which queue a board is about.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def board_get(
        ctx: Context[Any, AppContext],
        board_id: BoardID,
        fields: BoardFieldsParam = None,
    ) -> Board:
        board = await ctx.request_context.lifespan_context.boards.board_get(
            board_id,
            auth=get_yandex_auth(ctx),
        )

        if fields is not None:
            set_non_needed_fields_null([board], {f.name for f in fields})

        return board

    @mcp.tool(
        title="Get Board Columns",
        description="Get the columns of a Yandex Tracker agile board with the issue "
        "statuses mapped onto each - use it to see which status an issue needs to show "
        "up in a given column. Richer than the columns in `boards_get_all` / "
        "`board_get`, which carry no statuses.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def board_get_columns(
        ctx: Context[Any, AppContext],
        board_id: BoardID,
    ) -> list[BoardColumnDetail]:
        return await ctx.request_context.lifespan_context.boards.board_get_columns(
            board_id,
            auth=get_yandex_auth(ctx),
        )

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
        fields: SprintFieldsParam = None,
    ) -> list[Sprint]:
        sprints = await ctx.request_context.lifespan_context.boards.board_get_sprints(
            board_id,
            auth=get_yandex_auth(ctx),
        )

        if fields is not None:
            set_non_needed_fields_null(sprints, {f.name for f in fields})

        return sprints
