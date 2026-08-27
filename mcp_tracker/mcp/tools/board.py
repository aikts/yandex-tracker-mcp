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

# Page size for the walk `queue` needs. Walking a real organization's 415
# boards measured about the same total either way - 17 requests at 25, 9 at 50,
# 5 at 100 - with a per-request maximum that moved with the API's own variance
# rather than with the page size (9.1s at 50 against 3.5s at 100 in the same
# run). Fewest round trips for the same bytes is the only thing that separates
# them, so: 100.
BOARDS_SCAN_PAGE = 100

BoardFieldsParam = Annotated[
    list[BoardFieldsEnum] | None,
    Field(
        description="Fields to include in the response. In order to not pollute the "
        "context window - select appropriate fields beforehand. Not specifying fields "
        "will return all available. When looking for a board, id and name are usually "
        "enough; read the full record of the one board you need with `board_get`.",
    ),
]

SprintFieldsParam = Annotated[
    list[SprintFieldsEnum] | None,
    Field(
        description="Fields to include in the response. In order to not pollute the "
        "context window - select appropriate fields beforehand. Not specifying fields "
        "will return all available. Most of the time id, name and status are enough.",
    ),
]


def board_queue_keys(board: Board) -> set[str]:
    """Queue keys a board collects issues from, read off its own auto-filter.

    A board carries no queue field: what lands on it is whatever
    `addFilterSettings` matches, so the queue has to be read out of that filter.
    An inverted condition ("queue is not X") says which queue the board is
    *not* about and is therefore not a match.
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
        description="Get the agile boards (in russian - 'доски') available in Yandex Tracker. "
        "Use the returned board id with the `board_get`, `board_get_columns` and "
        "`board_get_sprints` tools. "
        "Pass `queue` to get only the boards that collect issues of that queue - "
        "that is the way to answer 'which board does this project use'. It matches "
        "the board's own filter, so it misses boards filtering by something else "
        "(personal boards, for one); to catch those, read a few issues of the queue "
        "with `issues_find` and look at their `boards` field. "
        "An organization can have hundreds of boards, so the listing is paginated: "
        "it returns a page of boards plus `next_cursor`, which you pass back as "
        "`cursor` to get the next one until it comes back null. Pass `fields` to "
        "keep the answer small while searching for the board you need. "
        "Boards are organization-wide and are NOT filtered by the server's queue "
        "allow-list: a board's settings can name a queue this server otherwise "
        "refuses to talk about.",
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
            # Tracker offers no server-side filter here - a board has no queue
            # field, it is matched by the queue in its own auto-filter - so a
            # match can be anywhere and the listing has to be walked. Walking it
            # a page at a time rather than asking for all of it at once is what
            # keeps every request the same size whatever the organization: the
            # unpaged endpoint is one request that grows without bound, and no
            # timeout covers both a small Tracker and a large one.
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
        "with its settings. `autoFilterSettings` is the board's own filter and tells "
        "which issues the board collects - read it to learn which queue a board is about. "
        "Also returns the columns, the field issues are estimated by and the working "
        "calendar the board uses.",
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
        description="Get the columns of a Yandex Tracker agile board together with the "
        "issue statuses mapped onto each of them. Use it to find out which status an "
        "issue has to be in to show up in a given column of the board. "
        "Richer than the columns nested in `boards_get_all` / `board_get`, which carry "
        "no statuses.",
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
