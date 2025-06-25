from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator

import dateutil.parser
from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import TextContent
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.helpers import dump_list, prepare_text_content
from mcp_tracker.mcp.params import IssueID, IssueIDs
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.types.queues import Queue

settings = Settings()


@asynccontextmanager
async def tracker_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    tracker = TrackerClient(
        token=settings.tracker_token,
        cloud_org_id=settings.tracker_cloud_org_id,
        org_id=settings.tracker_org_id,
    )

    queues: QueuesProtocol
    issues: IssueProtocol
    if settings.cache_enabled:
        queues_wrap, issues_wrap = make_cached_protocols(settings.cache_kwargs())
        queues = queues_wrap(tracker)
        issues = issues_wrap(tracker)
    else:
        queues = tracker
        issues = tracker

    try:
        yield AppContext(
            queues=queues,
            issues=issues,
        )
    finally:
        await tracker.close()


mcp = FastMCP(
    name="Yandex Tracker MCP Server",
    host=settings.host,
    port=settings.port,
    lifespan=tracker_lifespan,
)


def check_issue_id(issue_id: str) -> None:
    queue, _ = issue_id.split("-")
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise TrackerError(f"Issue `{issue_id}` not found.")


@mcp.tool(
    description="Find all Yandex Tracker queues available to the user (queue is a project in some sense)"
)
async def queues_get_all(
    ctx: Context[Any, AppContext],
) -> TextContent:
    result: list[Queue] = []
    per_page = 100
    page = 1

    while True:
        queues = await ctx.request_context.lifespan_context.queues.queues_list(
            per_page=per_page, page=page
        )
        if len(queues) == 0:
            break

        if settings.tracker_limit_queues:
            queues = [
                queue
                for queue in queues
                if queue.key in set(settings.tracker_limit_queues)
            ]

        result.extend(queues)
        page += 1

    return prepare_text_content(result)


@mcp.tool(description="Get a Yandex Tracker issue url by its id")
async def issue_get_url(
    issue_id: IssueID,
) -> TextContent:
    return prepare_text_content({"url": f"https://tracker.yandex.ru/{issue_id}"})


@mcp.tool(description="Get a Yandex Tracker issue by its id")
async def issue_get(
    ctx: Context[Any, AppContext],
    issue_id: IssueID,
) -> TextContent:
    check_issue_id(issue_id)

    issue = await ctx.request_context.lifespan_context.issues.issue_get(issue_id)
    if issue is None:
        raise TrackerError(f"Issue `{issue_id}` not found.")

    return prepare_text_content(issue)


@mcp.tool(description="Get comments of a Yandex Tracker issue by its id")
async def issue_get_comments(
    ctx: Context[Any, AppContext],
    issue_id: IssueID,
) -> TextContent:
    check_issue_id(issue_id)

    comments = await ctx.request_context.lifespan_context.issues.issue_get_comments(
        issue_id
    )
    if comments is None:
        raise TrackerError(f"Issue `{issue_id}` not found.")

    return prepare_text_content(comments)


@mcp.tool(
    description="Get a Yandex Tracker issue related links to other issues by its id"
)
async def issue_get_links(
    ctx: Context[Any, AppContext],
    issue_id: IssueID,
) -> TextContent:
    check_issue_id(issue_id)

    links = await ctx.request_context.lifespan_context.issues.issues_get_links(issue_id)
    if links is None:
        raise TrackerError(f"Issue `{issue_id}` not found.")

    return prepare_text_content(links)


@mcp.tool(description="Find Yandex Tracker issues by queue and/or created date")
async def issues_find(
    ctx: Context[Any, AppContext],
    queue: Annotated[
        str,
        Field(
            description="Queue (Project ID) to search in, like 'SOMEPROJECT'",
        ),
    ],
    created_from: Annotated[
        str | None,
        Field(
            None,
            description="Date to search from, in format YYYY-MM-DD",
        ),
    ],
    created_to: Annotated[
        str | None,
        Field(
            None,
            description="Date to search until, in format YYYY-MM-DD. It is non-inclusive",
        ),
    ],
    # per_page: Annotated[
    #     int,
    #     Field(
    #         description="Number of issues to return per page, default is 100",
    #     ),
    # ] = 100,
    page: Annotated[
        int,
        Field(
            description="Page number to return, default is 1",
        ),
    ] = 1,
) -> TextContent:
    per_page = 500

    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue}` not found or not allowed.")

    issues = await ctx.request_context.lifespan_context.issues.issues_find(
        queue,
        created_from=dateutil.parser.parse(created_from) if created_from else None,
        created_to=dateutil.parser.parse(created_to) if created_to else None,
        per_page=per_page,
        page=page,
    )

    return prepare_text_content(issues)


@mcp.tool(description="Get worklogs of a Yandex Tracker issue by its id")
async def issue_get_worklogs(
    ctx: Context[Any, AppContext],
    issue_ids: IssueIDs,
) -> TextContent:
    for issue_id in issue_ids:
        check_issue_id(issue_id)

    result: dict[str, Any] = {}
    for issue_id in issue_ids:
        worklogs = await ctx.request_context.lifespan_context.issues.issue_get_worklogs(
            issue_id
        )
        if not worklogs:
            result[issue_id] = []
        else:
            result[issue_id] = dump_list(worklogs)

    return prepare_text_content(result)
