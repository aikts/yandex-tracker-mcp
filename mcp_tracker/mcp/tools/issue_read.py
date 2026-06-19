"""Issue read-only MCP tools."""

import mimetypes
from pathlib import Path
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    CursorPerPageParam,
    IssueID,
    IssueIDs,
    PageParam,
    PerPageParam,
    YTQuery,
)
from mcp_tracker.mcp.tools._access import check_issue_access
from mcp_tracker.mcp.utils import (
    get_yandex_auth,
    save_issue_attachment_file,
    set_non_needed_fields_null,
)
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.issues import (
    ChangelogPage,
    ChecklistItem,
    DownloadedIssueAttachment,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueFieldsEnum,
    IssueLink,
    IssueTransition,
    Worklog,
)


def register_issue_read_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register issue read-only tools."""

    @mcp.tool(
        title="Get Issue",
        description="Get a Yandex Tracker issue by its id",
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
        description="Get comments of a Yandex Tracker issue by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_comments(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> list[IssueComment]:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_comments(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

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
        description="Find Yandex Tracker issues by queue and/or created date",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issues_find(
        ctx: Context[Any, AppContext],
        query: YTQuery,
        include_description: Annotated[
            bool,
            Field(
                description="Whether to include issue description in the issues result. It can be large, so use only when needed.",
            ),
        ] = False,
        fields: Annotated[
            list[IssueFieldsEnum] | None,
            Field(
                description="Fields to include in the response. In order to not pollute context window - select "
                "appropriate fields beforehand. Not specifying fields will return all available."
            ),
        ] = None,
        page: PageParam = 1,
        per_page: PerPageParam = 100,
    ) -> list[Issue]:
        issues = await ctx.request_context.lifespan_context.issues.issues_find(
            query=query,
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )

        if not include_description:
            for issue in issues:
                issue.description = None  # Clear description to save context

        if fields is not None:
            set_non_needed_fields_null(issues, {f.name for f in fields})

        return issues

    @mcp.tool(
        title="Count Issues",
        description="Get the count of Yandex Tracker issues matching a query",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issues_count(
        ctx: Context[Any, AppContext],
        query: YTQuery,
    ) -> int:
        return await ctx.request_context.lifespan_context.issues.issues_count(
            query,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Get Issue Worklogs",
        description="Get worklogs of a Yandex Tracker issue by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_worklogs(
        ctx: Context[Any, AppContext],
        issue_ids: IssueIDs,
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
    ) -> list[IssueAttachment]:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_attachments(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Download Issue Attachment",
        description=(
            "Download a Yandex Tracker issue attachment and save it to a local directory. "
            "Returns the absolute path to the saved file and its metadata."
        ),
    )
    async def issue_download_attachment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        attachment_id: str,
        file_name: str,
        save_directory: Annotated[
            str,
            Field(
                description=(
                    "Directory to save the downloaded file. "
                    "MUST be an absolute path, for example "
                    "/Users/me/projects/myproject/tmp/tracker-attachments/. "
                    "Relative paths resolve against the MCP server process cwd, "
                    "not your project, so pass an absolute path."
                ),
            ),
        ],
    ) -> DownloadedIssueAttachment:
        check_issue_access(settings, issue_id)

        data = await ctx.request_context.lifespan_context.issues.issue_download_attachment(
            issue_id,
            attachment_id,
            file_name,
            auth=get_yandex_auth(ctx),
        )

        local_path = save_issue_attachment_file(
            data,
            issue_id=issue_id,
            attachment_id=attachment_id,
            file_name=file_name,
            save_directory=save_directory,
        )
        safe_name = Path(file_name).name
        mime_type, _ = mimetypes.guess_type(safe_name)

        return DownloadedIssueAttachment(
            local_path=str(local_path),
            name=safe_name,
            mime_type=mime_type or "application/octet-stream",
            size=len(data),
        )

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
        description="Get the change history (changelog) of a Yandex Tracker issue by its id: "
        "status transitions, field edits (who changed what from -> to and when), "
        "comment changes and executed triggers. "
        "Returns a page of entries plus 'next_cursor'. To fetch the next page, pass "
        "'next_cursor' from the previous result as the 'cursor' argument; when "
        "'next_cursor' is null there are no more pages.",
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
