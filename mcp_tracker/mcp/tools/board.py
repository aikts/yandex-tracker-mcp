"""Board and sprint MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import BoardID, BoardQueueFilter, PageParam, PerPageParam
from mcp_tracker.mcp.tools._access import check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.boards import (
    Board,
    BoardColumnDetail,
    BoardFieldsEnum,
    Sprint,
    SprintFieldsEnum,
)

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
        if field.id != "queue" or field.value is None:
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
        "that is the way to answer 'which board does this project use'. "
        "An organization can have hundreds of boards, so the listing is paginated - "
        "keep increasing `page` until it comes back empty, and pass `fields` to keep "
        "the answer small while searching for the board you need.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def boards_get_all(
        ctx: Context[Any, AppContext],
        queue: BoardQueueFilter = None,
        fields: BoardFieldsParam = None,
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> list[Board]:
        if queue is not None:
            check_queue_access(settings, queue)

        boards = await ctx.request_context.lifespan_context.boards.boards_list(
            auth=get_yandex_auth(ctx),
        )

        # Tracker has no server-side filter here (`?queue=` is ignored along with
        # `page` / `perPage`), so the queue is matched against each board's own
        # auto-filter. Filtering runs before paging, or `page` would count boards
        # that are then dropped.
        if queue is not None:
            wanted = queue.upper()
            boards = [b for b in boards if wanted in board_queue_keys(b)]

        # `GET /v3/boards` ignores `page` / `perPage` and always answers with every
        # board, so the paging has to happen here. Left unbounded the tool returns
        # a quarter of a megabyte of JSON on a real organization, which is enough
        # to exhaust the caller's context on a single call.
        start = (page - 1) * per_page
        result = boards[start : start + per_page]

        if fields is not None:
            set_non_needed_fields_null(result, {f.name for f in fields})

        return result

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
