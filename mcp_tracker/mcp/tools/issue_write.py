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
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueComment,
    IssueLink,
    IssueLinkRelationship,
    IssueTransition,
    Worklog,
)


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

    @mcp.tool(
        title="Add Issue Comment",
        description="Add a comment to a Yandex Tracker issue. "
        "IMPORTANT: If you need to mention/call people to the discussion (so they get notifications), "
        "do NOT rely on '@login' in the text — use the `summonees` parameter instead.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_add_comment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        text: Annotated[
            str,
            Field(description="Comment text (markdown supported by Tracker)."),
        ],
        summonees: Annotated[
            list[str] | None,
            Field(
                description="Optional list of summoned users (logins or IDs). "
                "These users will be invited to the discussion and receive notifications "
                "(this is the API way to 'mention/call' someone in Yandex Tracker comments)."
            ),
        ] = None,
        maillist_summonees: Annotated[
            list[str] | None,
            Field(
                description="Optional list of mailing lists to summon (emails). "
                "Example: ['team@example.com']."
            ),
        ] = None,
        markup_type: Annotated[
            str | None,
            Field(
                description="Optional markup type for comment text. Use 'md' for YFM (markdown)."
            ),
        ] = None,
        is_add_to_followers: Annotated[
            bool,
            Field(
                description="Whether to add the comment author to issue followers. Default: true."
            ),
        ] = True,
    ) -> IssueComment:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_add_comment(
            issue_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            markup_type=markup_type,
            is_add_to_followers=is_add_to_followers,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Update Issue Comment",
        description="Update an existing comment in a Yandex Tracker issue. "
        "IMPORTANT: If you need to mention/call people (notifications), use the `summonees` parameter.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_update_comment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        comment_id: Annotated[
            int,
            Field(description="Comment ID (integer)."),
        ],
        text: Annotated[
            str,
            Field(description="New comment text (markdown supported by Tracker)."),
        ],
        summonees: Annotated[
            list[str] | None,
            Field(
                description="Optional list of summoned users (logins or IDs). "
                "These users will be invited to the discussion and receive notifications."
            ),
        ] = None,
        maillist_summonees: Annotated[
            list[str] | None,
            Field(
                description="Optional list of mailing lists to summon (emails). "
                "Example: ['team@example.com']."
            ),
        ] = None,
        markup_type: Annotated[
            str | None,
            Field(
                description="Optional markup type for comment text. Use 'md' for YFM (markdown)."
            ),
        ] = None,
    ) -> IssueComment:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_update_comment(
            issue_id,
            comment_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            markup_type=markup_type,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Move Issue to Another Queue",
        description="Move a Yandex Tracker issue to a different queue. "
        "The issue will receive a new key in the target queue (e.g., TASKS-1 → NEWQUEUE-42). "
        "Returns the updated issue with its new key and queue.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_move(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        queue: Annotated[
            str,
            Field(description="Target queue key (e.g., 'MYQUEUE')"),
        ],
        notify: Annotated[
            bool,
            Field(
                description="Whether users referenced in the issue's fields are notified "
                "of the change."
            ),
        ] = True,
        notify_author: Annotated[
            bool,
            Field(description="Whether the issue author is notified of the change."),
        ] = False,
        move_all_fields: Annotated[
            bool,
            Field(
                description="Whether to carry over the issue's versions, components and "
                "projects when matching ones exist in the target queue. When false, those "
                "fields are cleared."
            ),
        ] = False,
        initial_status: Annotated[
            bool,
            Field(
                description="Whether to reset the issue status to the initial value. "
                "Set this to true when moving to a queue with a different workflow. "
            ),
        ] = False,
    ) -> Issue:
        check_issue_access(settings, issue_id)
        check_queue_access(settings, queue)

        return await ctx.request_context.lifespan_context.issues.issue_move(
            issue_id,
            queue,
            notify=notify,
            notify_author=notify_author,
            move_all_fields=move_all_fields,
            initial_status=initial_status,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Issue Comment",
        description="Delete a comment from a Yandex Tracker issue",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_delete_comment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        comment_id: Annotated[
            int,
            Field(description="Comment ID (integer)."),
        ],
    ) -> None:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_delete_comment(
            issue_id,
            comment_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Issue Link",
        description="Create a link between a Yandex Tracker issue and another issue. "
        "The `relationship` describes how the current issue (issue_id) relates to the "
        "linked issue. For example, 'depends on' means issue_id depends on the linked "
        "issue, while 'is dependent by' means the linked issue depends on issue_id. "
        "Use 'relates' for a simple connection. Returns the created link.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_add_link(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        relationship: Annotated[
            IssueLinkRelationship,
            Field(
                description="Link type describing how the current issue (issue_id) "
                "relates to the linked issue. 'is epic of'/'has epic' apply only to "
                "Epic-type issues."
            ),
        ],
        issue: Annotated[
            str,
            Field(description="ID or key of the issue to link to, e.g. 'TEST-123'."),
        ],
    ) -> IssueLink:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_add_link(
            issue_id,
            relationship=relationship,
            issue=issue,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Issue Link",
        description="Delete a link between a Yandex Tracker issue and another issue. "
        "Use issue_get_links to retrieve the link IDs for an issue.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_delete_link(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        link_id: Annotated[
            int,
            Field(description="Link ID (integer) as returned by issue_get_links."),
        ],
    ) -> None:
        check_issue_access(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_delete_link(
            issue_id,
            link_id,
            auth=get_yandex_auth(ctx),
        )
