"""Issue write MCP tools (conditionally registered based on read-only mode)."""

import datetime
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import IssueID
from mcp_tracker.mcp.tools._access import check_issue_access, check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.inputs import (
    IssueUpdateFollower,
    IssueUpdateParent,
    IssueUpdatePriority,
    IssueUpdateProject,
    IssueUpdateSprint,
    IssueUpdateType,
)
from mcp_tracker.tracker.proto.types.issues import Issue, IssueTransition, Worklog


def register_issue_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register issue write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Execute Issue Transition",
        description="Execute a status transition for a Yandex Tracker issue. "
        "IMPORTANT: You MUST first call issue_get_transitions to retrieve available transitions for the issue. "
        "Only pass a transition_id that was returned by issue_get_transitions. "
        "Do NOT use arbitrary transition IDs - the API will reject invalid transition IDs. "
        "Returns a list of new transitions available for the issue in its new status.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_execute_transition(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        transition_id: Annotated[
            str,
            Field(
                description="The transition ID to execute. Must be one of the IDs returned by issue_get_transitions tool."
            ),
        ],
        comment: Annotated[
            str | None,
            Field(description="Optional comment to add when executing the transition."),
        ] = None,
        fields: Annotated[
            dict[str, str | int | list[str]] | None,
            Field(
                description="Optional dictionary of additional fields to set during the transition. "
                "Common fields include 'resolution' (e.g., 'fixed', 'wontFix') for closing issues, "
                "'assignee' for reassigning, etc."
            ),
        ] = None,
    ) -> list[IssueTransition]:
        check_issue_access(settings, issue_id)

        return (
            await ctx.request_context.lifespan_context.issues.issue_execute_transition(
                issue_id,
                transition_id,
                comment=comment,
                fields=fields,
                auth=get_yandex_auth(ctx),
            )
        )

    @mcp.tool(
        title="Close Issue",
        description="Close a Yandex Tracker issue with a resolution. "
        "This is a convenience tool that automatically finds a transition to a 'done' status "
        "and executes it with the specified resolution. "
        "IMPORTANT: Before closing, you MUST: "
        "1) Call issue_get to retrieve the issue's type field. "
        "2) Call queue_get_metadata with expand=['issueTypesConfig'] to get available resolutions. "
        "3) Choose a resolution from the issueTypesConfig entry matching the issue's type - "
        "each issue type has its own set of valid resolutions. "
        "Returns a list of transitions available for the issue in its new (closed) status.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_close(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        resolution_id: Annotated[
            str,
            Field(
                description="The resolution ID to set when closing the issue. "
                "Must be one of the IDs returned by get_resolutions tool (e.g., 'fixed', 'wontFix', 'duplicate')."
            ),
        ],
        fields: Annotated[
            dict[str, str | int | list[str]] | None,
            Field(
                description="Optional dictionary of additional fields to set during the transition. "
                "Common fields include 'resolution' (e.g., 'fixed', 'wontFix') for closing issues, "
                "'assignee' for reassigning, etc."
            ),
        ] = None,
        comment: Annotated[
            str | None,
            Field(description="Optional comment to add when closing the issue."),
        ] = None,
    ) -> list[IssueTransition]:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_close(
            issue_id,
            resolution_id,
            comment=comment,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Create Issue",
        description="Create a new issue in a Yandex Tracker queue",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_create(
        ctx: Context[Any, AppContext],
        queue: Annotated[
            str,
            Field(description="Queue key where to create the issue (e.g., 'MYQUEUE')"),
        ],
        summary: Annotated[str, Field(description="Issue title/summary")],
        type: Annotated[
            int | None,
            Field(description="Issue type id (from get_issue_types tool)"),
        ] = None,
        description: Annotated[
            str | None, Field(description="Issue description")
        ] = None,
        assignee: Annotated[
            str | int | None, Field(description="Assignee login or UID")
        ] = None,
        priority: Annotated[
            str | None,
            Field(description="Priority key (from get_priorities tool,)"),
        ] = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description="Additional fields to set during issue creation. "
                "IMPORTANT: Before creating an issue, you MUST call `queue_get_fields` to get available fields "
                "(it returns both global and local fields by default). "
                "Fields with schema.required=true are mandatory and must be provided. "
                "Use the field's `id` property as the key in this map (e.g., {'fieldId': 'value'})."
            ),
        ] = None,
    ) -> Issue:
        check_queue_access(settings, queue)
        return await ctx.request_context.lifespan_context.issues.issue_create(
            queue=queue,
            summary=summary,
            type=type,
            description=description,
            assignee=assignee,
            priority=priority,
            auth=get_yandex_auth(ctx),
            **(fields or {}),
        )

    @mcp.tool(
        title="Update Issue",
        description="Update an existing Yandex Tracker issue. "
        "Only fields that are provided will be updated; omitted fields remain unchanged. "
        "Use queue_get_fields to discover available fields before updating.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_update(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        summary: Annotated[
            str | None,
            Field(description="New issue title/summary"),
        ] = None,
        description: Annotated[
            str | None,
            Field(description="New issue description (use markdown formatting)"),
        ] = None,
        markup_type: Annotated[
            str,
            Field(
                description="Markup type for description text. Use 'md' for YFM (markdown) markup."
            ),
        ] = "md",
        parent: Annotated[
            IssueUpdateParent | None,
            Field(
                description="Parent issue reference. Object with 'id' (parent issue ID) "
                "and/or 'key' (parent issue key like 'QUEUE-123')."
            ),
        ] = None,
        sprint: Annotated[
            list[IssueUpdateSprint] | None,
            Field(
                description="Sprint assignments. Array of objects, each with 'id' field "
                "containing the sprint ID (integer)."
            ),
        ] = None,
        type: Annotated[
            IssueUpdateType | None,
            Field(
                description="Issue type. Object with 'id' (type ID) and/or 'key' (type key like 'bug', 'task'). "
                "Use `queue_get_metadata` tool with expand=['issueTypesConfig'] to get available issue types in this queue."
            ),
        ] = None,
        priority: Annotated[
            IssueUpdatePriority | None,
            Field(
                description="Issue priority. Object with 'id' (priority ID) and/or 'key' "
                "(priority key like 'critical', 'normal'). Use get_priorities to find available priorities."
            ),
        ] = None,
        followers: Annotated[
            list[IssueUpdateFollower] | None,
            Field(
                description="Issue followers/watchers. Array of objects, each with 'id' field "
                "containing the user ID or login."
            ),
        ] = None,
        project: Annotated[
            IssueUpdateProject | None,
            Field(
                description="Project assignment. Object with 'primary' (int, main project shortId) "
                "and optional 'secondary' (list of ints, additional project shortIds)."
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Field(description="Issue tags as array of strings."),
        ] = None,
        version: Annotated[
            int | None,
            Field(
                description="Issue version for optimistic locking. "
                "Changes are only made to the current version of the issue. Always try to receive issue's version using issue_get tool first."
            ),
        ] = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description="Additional fields to update. "
                "Use queue_get_fields to discover available fields. "
                "Use the field's 'id' property as the key (e.g., {'fieldId': 'value'})."
            ),
        ] = None,
    ) -> Issue:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_update(
            issue_id,
            summary=summary,
            description=description,
            markup_type=markup_type,
            parent=parent,
            sprint=sprint,
            type=type,
            priority=priority,
            followers=followers,
            project=project,
            tags=tags,
            version=version,
            auth=get_yandex_auth(ctx),
            **(fields or {}),
        )

    @mcp.tool(
        title="Add Worklog",
        description="Add a worklog entry (log spent time) to a Yandex Tracker issue",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_add_worklog(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        duration: Annotated[
            str,
            Field(
                description="Time spent in ISO-8601 duration format (e.g., 'PT1H30M').",
            ),
        ],
        comment: Annotated[
            str | None,
            Field(description="Optional comment to add to the worklog entry."),
        ] = None,
        start: Annotated[
            datetime.datetime | None,
            Field(
                description="Optional start datetime for the worklog. "
                "If timezone is not provided, UTC is assumed."
            ),
        ] = None,
    ) -> Worklog:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_add_worklog(
            issue_id,
            duration=duration,
            comment=comment,
            start=start,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Worklog",
        description="Update a worklog entry (spent time record) in a Yandex Tracker issue",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_update_worklog(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        worklog_id: Annotated[
            int,
            Field(description="Worklog entry ID (integer)."),
        ],
        duration: Annotated[
            str | None,
            Field(
                description="New time spent in ISO-8601 duration format (e.g., 'PT1H30M').",
            ),
        ] = None,
        comment: Annotated[
            str | None,
            Field(description="New comment for the worklog entry."),
        ] = None,
        start: Annotated[
            datetime.datetime | None,
            Field(
                description="New start datetime for the worklog. "
                "If timezone is not provided, UTC is assumed."
            ),
        ] = None,
    ) -> Worklog:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_update_worklog(
            issue_id,
            worklog_id,
            duration=duration,
            comment=comment,
            start=start,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Worklog",
        description="Delete a worklog entry (spent time record) from a Yandex Tracker issue",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_delete_worklog(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        worklog_id: Annotated[
            int,
            Field(description="Worklog entry ID (integer)."),
        ],
    ) -> None:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_delete_worklog(
            issue_id,
            worklog_id,
            auth=get_yandex_auth(ctx),
        )
