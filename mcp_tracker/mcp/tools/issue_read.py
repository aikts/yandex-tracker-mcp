"""Issue read-only MCP tools."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    CommentsCursorParam,
    CursorPerPageParam,
    IssueID,
    IssueIDs,
    PageParam,
    PerPageParam,
    YTQuery,
)
from mcp_tracker.mcp.tools._access import check_issue_access
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.issues import (
    AttachmentFieldsEnum,
    ChangelogPage,
    ChecklistItem,
    CommentFieldsEnum,
    CommentsPage,
    Issue,
    IssueAttachment,
    IssueLink,
    IssuesCount,
    IssueTransition,
    Worklog,
    WorklogFieldsEnum,
    resolve_issue_field,
)
from mcp_tracker.tracker.proto.types.pagination import PaginatedResult


def register_issue_read_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register issue read-only tools."""

    @mcp.tool(
        title="Get Issue",
        description="Get a Yandex Tracker issue by its id: read one issue (task, "
        "ticket, bug) with a known key like 'QUEUE-123' and return its full record - "
        "summary, description, status, type, priority, assignee, dates, tags, "
        "components, sprint, parent, estimates, the current `version` and any "
        "queue-local or custom fields. Use it to inspect a single issue you can "
        "already name, and to read a fresh `version` right before `issue_update`. To "
        "search instead of reading a known issue, use `issues_find`. Comments, links, "
        "attachments, worklogs, checklist, changelog and transitions are not included "
        "- each has its own `issue_get_*` tool.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        include_description: Annotated[
            bool,
            Field(
                description="Whether to include issue description in the issues result. "
                "It can be large, so use only when needed.",
            ),
        ] = True,
    ) -> Issue:
        check_issue_access(settings, issue_id)

        issue = await ctx.request_context.lifespan_context.issues.issue_get(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

        if not include_description:
            issue.description = None

        return issue

    @mcp.tool(
        title="Get Issue Comments",
        description="Get a page of comments of a Yandex Tracker issue by its id. "
        "Returns the comments plus `next_cursor` - pass it back as `cursor` until it "
        "is null.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_comments(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        per_page: CursorPerPageParam = 50,
        cursor: CommentsCursorParam = None,
        fields: Annotated[
            list[CommentFieldsEnum] | None,
            Field(
                description="Fields to include in each comment; omit to get all. "
                "text/text_html can be large, so select only what you need.",
            ),
        ] = None,
    ) -> CommentsPage:
        check_issue_access(settings, issue_id)

        page = await ctx.request_context.lifespan_context.issues.issue_get_comments(
            issue_id,
            per_page=per_page,
            cursor=cursor,
            auth=get_yandex_auth(ctx),
        )

        if fields is not None:
            set_non_needed_fields_null(page.comments, {f.name for f in fields})

        return page

    @mcp.tool(
        title="Get Issue Links",
        description="Get a Yandex Tracker issue related links to other issues by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_links(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> list[IssueLink]:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issues_get_links(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Find Issues",
        description="Find Yandex Tracker issues matching a Yandex Tracker Query (YQL) - not limited to "
        "queue/date, any indexed field can be used (assignee, status, tags, etc., see the `query` "
        "parameter for the full syntax).",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issues_find(
        ctx: Context[Any, AppContext],
        query: YTQuery,
        include_description: Annotated[
            bool,
            Field(
                description="Whether to include the issue description; it can be large. "
                "Ignored when `description` is listed in `fields`.",
            ),
        ] = False,
        fields: Annotated[
            list[str] | None,
            Field(
                description="Fields to return, in Tracker's own spelling "
                "(`storyPoints`, not `story_points`); the standard ones are in this "
                "tool's output schema. For a queue's local or the organization's "
                "custom fields, pass the field `id` from `queue_get_fields`. An "
                "unknown name is dropped silently, so check there if a field comes "
                "back missing. Omitting this returns ALL fields."
            ),
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 100,
    ) -> PaginatedResult[Issue]:
        api_fields: list[str] | None = None
        selected: set[str] | None = None
        if fields is not None:
            resolved = [resolve_issue_field(name) for name in fields]
            # Asking for both spellings of one field would send it to the API twice.
            api_fields = list(dict.fromkeys(api for api, _ in resolved))
            selected = {key for _, key in resolved}

        result = await ctx.request_context.lifespan_context.issues.issues_find(
            query=query,
            per_page=per_page,
            page=page,
            fields=api_fields,
            auth=get_yandex_auth(ctx),
        )

        # A description asked for through `fields` is an explicit request for it,
        # so it is not stripped by `include_description` defaulting to False.
        if not include_description and "description" not in (selected or ()):
            for issue in result.values:
                issue.description = None  # Clear description to save context

        if selected is not None:
            # Tracker sends `self`, `id`, `version` and `favorite` on top of any
            # projection, so the response still needs trimming to what was asked for.
            set_non_needed_fields_null(result.values, selected)

        return result

    @mcp.tool(
        title="Count Issues",
        description="Get the count of Yandex Tracker issues matching a query.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issues_count(
        ctx: Context[Any, AppContext],
        query: YTQuery,
    ) -> IssuesCount:
        count = await ctx.request_context.lifespan_context.issues.issues_count(
            query,
            auth=get_yandex_auth(ctx),
        )
        return IssuesCount(count=count)

    @mcp.tool(
        title="Get Issue Worklogs",
        description="Get worklogs of a Yandex Tracker issue by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_worklogs(
        ctx: Context[Any, AppContext],
        issue_ids: IssueIDs,
        fields: Annotated[
            list[WorklogFieldsEnum] | None,
            Field(
                description="Fields to include in each worklog entry; omit to get all. "
                "Select only what you need.",
            ),
        ] = None,
    ) -> dict[str, list[Worklog]]:
        for issue_id in issue_ids:
            check_issue_access(settings, issue_id)

        result: dict[str, list[Worklog]] = {}
        for issue_id in issue_ids:
            worklogs = (
                await ctx.request_context.lifespan_context.issues.issue_get_worklogs(
                    issue_id,
                    auth=get_yandex_auth(ctx),
                )
            )
            if fields is not None and worklogs:
                set_non_needed_fields_null(worklogs, {f.name for f in fields})
            result[issue_id] = worklogs or []

        return result

    @mcp.tool(
        title="Get Issue Attachments",
        description="Get attachments of a Yandex Tracker issue by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_attachments(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        fields: Annotated[
            list[AttachmentFieldsEnum] | None,
            Field(
                description="Fields to include in each attachment; omit to get all. "
                "The 'content' field can be large, so select only what you need.",
            ),
        ] = None,
    ) -> list[IssueAttachment]:
        check_issue_access(settings, issue_id)

        attachments = (
            await ctx.request_context.lifespan_context.issues.issue_get_attachments(
                issue_id,
                auth=get_yandex_auth(ctx),
            )
        )

        if fields is not None:
            set_non_needed_fields_null(attachments, {f.name for f in fields})

        return attachments

    @mcp.tool(
        title="Get Issue Checklist",
        description="Get checklist items of a Yandex Tracker issue by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_checklist(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> list[ChecklistItem]:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_checklist(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Issue Transitions",
        description="Get possible status transitions for a Yandex Tracker issue. "
        "Returns list of available transitions that can be performed on the issue.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_transitions(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> list[IssueTransition]:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_transitions(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Issue Changelog",
        description="Get the change history (changelog) of a Yandex Tracker issue: "
        "status transitions, field edits (who changed what from -> to and when), "
        "comment changes and executed triggers. Returns a page of entries plus "
        "`next_cursor` - pass it back as `cursor` until it is null.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_changelog(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        per_page: CursorPerPageParam = 50,
        cursor: Annotated[
            str | None,
            Field(
                description="Cursor for the next page: the 'next_cursor' value returned by "
                "the previous call. Leave empty for the first page.",
            ),
        ] = None,
        field: Annotated[
            str | None,
            Field(
                description="Optional field key to filter the changelog by "
                "(e.g. 'status' to only see status changes).",
            ),
        ] = None,
        type: Annotated[
            str | None,
            Field(
                description="Optional change type to filter by (e.g. 'IssueWorkflow' for status transitions).",
            ),
        ] = None,
    ) -> ChangelogPage:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_changelog(
            issue_id,
            per_page=per_page,
            cursor=cursor,
            field=field,
            type=type,
            auth=get_yandex_auth(ctx),
        )
