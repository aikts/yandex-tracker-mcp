from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import TextContent
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.helpers import dump_list, prepare_text_content
from mcp_tracker.mcp.params import IssueID, IssueIDs, QueueID
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
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

    queues: QueuesProtocol = tracker
    issues: IssueProtocol = tracker
    fields: GlobalDataProtocol = tracker
    if settings.cache_enabled:
        queues_wrap, issues_wrap, fields_wrap = make_cached_protocols(
            settings.cache_kwargs()
        )
        queues = queues_wrap(queues)
        issues = issues_wrap(issues)
        fields = fields_wrap(fields)

    try:
        yield AppContext(
            queues=queues,
            issues=issues,
            fields=fields,
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


@mcp.tool(
    description="Get local fields for a specific Yandex Tracker queue (queue-specific custom fields)"
)
async def queue_get_local_fields(
    ctx: Context[Any, AppContext],
    queue_id: QueueID,
) -> TextContent:
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

    fields = await ctx.request_context.lifespan_context.queues.queues_get_local_fields(
        queue_id
    )
    return prepare_text_content(fields)


@mcp.tool(
    description="Get all global fields available in Yandex Tracker that can be used in issues"
)
async def get_global_fields(
    ctx: Context[Any, AppContext],
) -> TextContent:
    fields = await ctx.request_context.lifespan_context.fields.get_global_fields()
    return prepare_text_content(fields)


@mcp.tool(
    description="Get all statuses available in Yandex Tracker that can be used in issues"
)
async def get_statuses(
    ctx: Context[Any, AppContext],
) -> TextContent:
    statuses = await ctx.request_context.lifespan_context.fields.get_statuses()
    return prepare_text_content(statuses)


@mcp.tool(
    description="Get all issue types available in Yandex Tracker that can be used when creating or updating issues"
)
async def get_issue_types(
    ctx: Context[Any, AppContext],
) -> TextContent:
    issue_types = await ctx.request_context.lifespan_context.fields.get_issue_types()
    return prepare_text_content(issue_types)


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
    query: Annotated[
        str,
        Field(
            description=(
                """Search query to filter issues using Yandex Tracker Query Language, Instructions:\n"""
                """# General instructions\n"""
                """1. To search by a specific field use the following syntax: `Description: "some issue description"`\n"""
                """2. Multiple fields should be separated by space: `Description: "some issue description" Created: today()`\n"""
                """3. If you need to specify multiple values for the same field - provide them using comma (,), e.g.: `author: "vpupkin","iivanov"`\n"""
                """4. You may specify multiple conditions and combine them using `AND` and `OR` statements, e.g. `<param_1>: "<value_1>" AND <param_2>: "<value_2>"`\n"""
                """5. You may use brackets for complex logical expressions\n"""
                """6. To find issues with exact string matching in the field use this syntax: `Summary: #"Version 2.0"`. If you need to pass special characters - you must escape them using `\\` symbol\n"""
                """7. To find issues that don't contain the specified text use this syntax: `Summary: !"Version 2.0"`. If you need to pass special characters - you must escape them using `\\` symbol\n"""
                """8. If you need to search by local queue field use the following syntax: `<QUEUE>.<LOCAL_FIELD_KEY>: "<value>", where <QUEUE> is a queue key, <LOCAL_FIELD_KEY> is a local field's key from the `queue_get_local_fields` tool result.\n"""
                """9. For dates use the format YYYY-MM-DD.\n"""
                """10. For numerical values you may use comparison operators (>, <, >=, <=): `<param>: ><value>`.\n"""
                """11. To sort the result specify the `Sort By` directive (you may provide ASC or DESC for the sort order): `"Sort By": Created ASC`.\n"""
                """# Functions\n"""
                """These functions may be used, for example: `Created: week()` - return issues created on the current week"\n"""
                """* `empty()` - empty value\n"""
                """* `notEmpty()` - not empty value\n"""
                """* `now()` - current time\n"""
                """* `today()` - current date\n"""
                """* `week()` - current week\n"""
                """* `month()` - current month\n"""
                """* `quarter()` - current quarter\n"""
                """* `year()` - current year\n"""
                """* `unresolved()` - there is no resolution\n"""
                """# Examples\n"""
                """Find issues in a specific queue: `"Queue": "PROJ"`\n"""
                """Find issues by an assignee: `"Assignee": "Иван Иванов"`\n"""
                """Find issues in specific status: `"Status": "Открыт", "В работе"`\n"""
                """Find issues created in a specific range: `"Created": "2017-01-01".."2017-01-30"`\n"""
                """Find issues created no earlier than 1 week and 1 day before today: `Created: > today() - "1w 1d"`\n"""
            )
        ),
    ],
    page: Annotated[
        int,
        Field(
            description="Page number to return, default is 1",
        ),
    ] = 1,
) -> TextContent:
    per_page = 500

    issues = await ctx.request_context.lifespan_context.issues.issues_find(
        query=query,
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
