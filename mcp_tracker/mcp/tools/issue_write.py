"""Issue write MCP tools (conditionally registered based on read-only mode)."""

import datetime
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ClientCapabilities, ElicitationCapability, ToolAnnotations
from pydantic import BaseModel, Field, create_model

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.params import (
    IssueChecklistItemAssigneeParam,
    IssueChecklistItemCheckedParam,
    IssueChecklistItemDeadlineParam,
    IssueChecklistItemIDParam,
    IssueChecklistItemsParam,
    IssueChecklistItemTextParam,
    IssueComponentsParam,
    IssueComponentsUpdateParam,
    IssueFollowersParam,
    IssueFollowersUpdateParam,
    IssueID,
    IssueParentParam,
    IssueProjectParam,
    IssueSprintParam,
    IssueTagsParam,
    MarkupTypeParam,
)
from mcp_tracker.mcp.tools._access import check_issue_access, check_queue_access
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.inputs import (
    IssuePriorityRef,
    IssueTypeRef,
)
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueComment,
    IssueLink,
    IssueLinkRelationship,
    IssueTransition,
    Worklog,
)


def _build_move_options_schema(
    *,
    notify: bool,
    notify_author: bool,
    move_all_fields: bool,
    initial_status: bool,
) -> type[BaseModel]:
    """Build an elicitation schema for issue_move's boolean options.

    Defaults are seeded with the values the caller passed so the elicitation
    form is pre-filled with them and the user only adjusts what they need to.
    """
    return create_model(
        "IssueMoveOptions",
        notify=(
            bool,
            Field(
                default=notify,
                description="Notify users referenced in the issue's fields of the move.",
            ),
        ),
        notify_author=(
            bool,
            Field(
                default=notify_author,
                description="Notify the issue author of the move.",
            ),
        ),
        move_all_fields=(
            bool,
            Field(
                default=move_all_fields,
                description="Carry over versions, components and projects when matching "
                "ones exist in the target queue (otherwise they are cleared).",
            ),
        ),
        initial_status=(
            bool,
            Field(
                default=initial_status,
                description="Reset the issue status to the initial value (use when the "
                "target queue has a different workflow).",
            ),
        ),
    )


def register_issue_write_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register issue write tools (not registered in read-only mode)."""

    @mcp.tool(
        title="Execute Issue Transition",
        description="Execute a status transition for a Yandex Tracker issue. Call "
        "`issue_get_transitions` first and pass one of the ids it returned - the API "
        "rejects anything else. Returns the transitions available in the new status.",
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
        check_issue_access(settings, issue_id, write=True)

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
        description="Close a Yandex Tracker issue with a resolution: finds a "
        "transition to a 'done' status and executes it. The resolution has to be one "
        "the issue's type allows - read the type with `issue_get`, then call "
        "`queue_get_metadata` with expand=['issueTypesConfig'] for the resolutions of "
        "that type. Returns the transitions available in the new (closed) status.",
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
                description="Optional dictionary of additional fields to set during the transition "
                "(e.g. 'assignee' for reassigning). Do NOT set 'resolution' here - use the dedicated "
                "resolution_id parameter instead."
            ),
        ] = None,
        comment: Annotated[
            str | None,
            Field(description="Optional comment to add when closing the issue."),
        ] = None,
    ) -> list[IssueTransition]:
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_close(
            issue_id,
            resolution_id,
            comment=comment,
            fields=fields,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Create Issue",
        description="Create a new issue in a Yandex Tracker queue. There is no "
        "`template_id` parameter: check the queue's templates first "
        "(`issue_templates_get_all` with `queue` set) and copy their `fieldTemplates` "
        "values into the parameters below field by field - `assignee` arrives as a "
        "user object while this tool takes a login or uid, and template macros such as "
        "`{{today}}` arrive literally. Prefer the dedicated parameters over the "
        "`fields` map. The returned `version` goes stale immediately, as queue "
        "triggers run right after creation: re-read the issue with `issue_get` instead "
        "of feeding it to `issue_update`.",
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
            IssueTypeRef | str | int | None,
            Field(
                description="Issue type: an object with 'id' (type ID) and/or 'key' "
                "(e.g., 'bug', 'task'), or the bare key/ID (from get_issue_types tool)."
            ),
        ] = None,
        description: Annotated[
            str | None, Field(description="Issue description (use markdown formatting)")
        ] = None,
        markup_type: MarkupTypeParam = "md",
        assignee: Annotated[
            str | int | None, Field(description="Assignee login or UID")
        ] = None,
        priority: Annotated[
            IssuePriorityRef | str | int | None,
            Field(
                description="Issue priority: an object with 'id' (priority ID) and/or 'key' "
                "(e.g., 'critical', 'normal'), or the bare key/ID (from get_priorities tool)."
            ),
        ] = None,
        parent: IssueParentParam = None,
        sprint: IssueSprintParam = None,
        followers: IssueFollowersParam = None,
        components: IssueComponentsParam = None,
        tags: IssueTagsParam = None,
        project: IssueProjectParam = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description="Additional fields to set, for those without a dedicated "
                "parameter above. Field ids come from `queue_get_fields` "
                "(schema.required=true marks the mandatory ones) or "
                "`get_global_fields`, which also lists system fields such as `parent` "
                "or `estimation` that the queue listing may omit. Keys are Tracker's "
                "own camelCase ids, e.g. 'storyPoints'. An entry here overrides the "
                "dedicated parameter of the same name. Values are sent as-is: "
                "reference fields want numeric IDs as numbers or {'id': ...} objects, "
                "since a bare string may be read as a name."
            ),
        ] = None,
    ) -> Issue:
        check_queue_access(settings, queue, write=True)
        return await ctx.request_context.lifespan_context.issues.issue_create(
            queue=queue,
            summary=summary,
            type=type,
            description=description,
            markup_type=markup_type,
            assignee=assignee,
            priority=priority,
            parent=parent,
            sprint=sprint,
            followers=followers,
            components=components,
            tags=tags,
            project=project,
            auth=get_yandex_auth(ctx),
            fields=fields,
        )

    @mcp.tool(
        title="Update Issue",
        description="Update an existing Yandex Tracker issue. Only the parameters you "
        "pass change; the rest stay as they are. Use `queue_get_fields` to discover "
        "the queue's fields. `version` is optional optimistic locking - pass one read "
        "moments earlier with `issue_get`, never the one `issue_create` returned, "
        "since triggers bump it right after creation.",
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
        markup_type: MarkupTypeParam = "md",
        parent: IssueParentParam = None,
        sprint: IssueSprintParam = None,
        type: Annotated[
            IssueTypeRef | str | int | None,
            Field(
                description="Issue type. Object with 'id' (type ID) and/or 'key' (type key like 'bug', 'task'), "
                "or the bare key/ID. "
                "Use `queue_get_metadata` tool with expand=['issueTypesConfig'] to get available issue types in this queue."
            ),
        ] = None,
        priority: Annotated[
            IssuePriorityRef | str | int | None,
            Field(
                description="Issue priority. Object with 'id' (priority ID) and/or 'key' "
                "(priority key like 'critical', 'normal'), or the bare key/ID. "
                "Use get_priorities to find available priorities."
            ),
        ] = None,
        assignee: Annotated[
            str | int | None,
            Field(description="New assignee login or UID"),
        ] = None,
        followers: IssueFollowersUpdateParam = None,
        components: IssueComponentsUpdateParam = None,
        project: IssueProjectParam = None,
        tags: IssueTagsParam = None,
        version: Annotated[
            int | None,
            Field(
                description="Issue version for optimistic locking: the change lands "
                "only if this is the issue's current version, otherwise the call fails "
                "with an editing conflict. Read it with `issue_get` right before "
                "updating, or omit it to update whatever the latest version is. The "
                "version `issue_create` returned is not safe here - triggers bump it "
                "right after creation."
            ),
        ] = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description="Additional fields to update, for those without a "
                "dedicated parameter above. Field ids come from `queue_get_fields` or "
                "`get_global_fields`, which also lists system fields such as `parent` "
                "or `estimation` that the queue listing may omit. Keys are Tracker's "
                "own camelCase ids, e.g. 'storyPoints'. An entry here overrides the "
                "dedicated parameter of the same name, which is how a field is "
                "cleared: pass null (e.g. {'assignee': null}), since a dedicated "
                "parameter left unset is simply not sent. Values are sent as-is: "
                "reference fields want numeric IDs as numbers or {'id': ...} objects, "
                "since a bare string may be read as a name."
            ),
        ] = None,
    ) -> Issue:
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_update(
            issue_id,
            summary=summary,
            description=description,
            markup_type=markup_type,
            parent=parent,
            sprint=sprint,
            type=type,
            priority=priority,
            assignee=assignee,
            followers=followers,
            components=components,
            project=project,
            tags=tags,
            version=version,
            auth=get_yandex_auth(ctx),
            fields=fields,
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
        check_issue_access(settings, issue_id, write=True)

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
        check_issue_access(settings, issue_id, write=True)

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
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_delete_worklog(
            issue_id,
            worklog_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Issue Comment",
        description="Add a comment to a Yandex Tracker issue. There is no "
        "`template_id` parameter: check `comment_templates_get_all` (with `queue` set) "
        "first and copy the template's `template` text into `text` and its summonees "
        "into the parameters below. To mention or call people so they get notified, "
        "use `summonees` - '@login' in the text notifies nobody.",
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
                description="Users to summon (logins or IDs): they are invited to the "
                "discussion and notified. This is the API way to 'mention/call' "
                "someone in a Yandex Tracker comment."
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
        check_issue_access(settings, issue_id, write=True)

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
        description="Update an existing comment in a Yandex Tracker issue. To mention "
        "or call people, use `summonees`, not '@login' in the text.",
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
                description="Users to summon (logins or IDs): they are invited to the "
                "discussion and notified. This is the API way to 'mention/call' "
                "someone in a Yandex Tracker comment."
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
        check_issue_access(settings, issue_id, write=True)

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
        check_issue_access(settings, issue_id, write=True)
        check_queue_access(settings, queue, write=True)

        # When the client supports elicitation, confirm the boolean options with
        # the user before performing the (irreversible) move. The form is seeded
        # with the values passed by the caller so the user only adjusts what they
        # need to. Clients without elicitation support fall back to those values.
        if ctx.session.check_client_capability(
            ClientCapabilities(elicitation=ElicitationCapability())
        ):
            options_schema = _build_move_options_schema(
                notify=notify,
                notify_author=notify_author,
                move_all_fields=move_all_fields,
                initial_status=initial_status,
            )
            elicitation = await ctx.elicit(
                message=f"Confirm the options for moving issue {issue_id} to queue {queue}.",
                schema=options_schema,
            )
            if elicitation.action != "accept":
                raise TrackerError(
                    f"Move of issue `{issue_id}` to queue `{queue}` was cancelled by the user."
                )

            options = elicitation.data.model_dump()
            notify = options["notify"]
            notify_author = options["notify_author"]
            move_all_fields = options["move_all_fields"]
            initial_status = options["initial_status"]

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
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_delete_comment(
            issue_id,
            comment_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Issue Link",
        description="Create a link between a Yandex Tracker issue and another issue. "
        "`relationship` reads from the current issue: 'depends on' means issue_id "
        "depends on the linked issue, 'is dependent by' is the reverse, 'relates' is a "
        "plain connection.",
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
        check_issue_access(settings, issue_id, write=True)

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
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_delete_link(
            issue_id,
            link_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Add Issue Checklist Items",
        description="Add one or more items to the checklist of a Yandex Tracker issue. "
        "The checklist is created if the issue does not have one yet, and items are "
        "appended in the order given. Returns the issue's checklist after the items "
        "were added.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_add_checklist_items(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        items: IssueChecklistItemsParam,
    ) -> list[ChecklistItem]:
        check_issue_access(settings, issue_id, write=True)

        return (
            await ctx.request_context.lifespan_context.issues.issue_add_checklist_items(
                issue_id,
                items=items,
                auth=get_yandex_auth(ctx),
            )
        )

    @mcp.tool(
        title="Update Issue Checklist Item",
        description="Update a single checklist item of a Yandex Tracker issue, e.g. to "
        "mark it as checked. Only the fields you pass are changed - the ones you omit "
        "keep their current value, so this tool cannot clear a field: passing null (or "
        "an empty value) for `assignee` or `deadline` leaves it as it is instead of "
        "removing it. Delete and re-add the item to drop an assignee or a deadline. "
        "At least one of text/checked/assignee/deadline must be passed. Omitting "
        "text keeps the item's current text - you do not need to resend it. Use "
        "issue_get_checklist to get the item IDs. "
        "Returns the issue's checklist after the change.",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_update_checklist_item(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        checklist_item_id: IssueChecklistItemIDParam,
        text: IssueChecklistItemTextParam = None,
        checked: IssueChecklistItemCheckedParam = None,
        assignee: IssueChecklistItemAssigneeParam = None,
        deadline: IssueChecklistItemDeadlineParam = None,
    ) -> list[ChecklistItem]:
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_update_checklist_item(
            issue_id,
            checklist_item_id,
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=deadline,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Delete Issue Checklist Item",
        description="Delete a single item from the checklist of a Yandex Tracker issue. "
        "Use issue_get_checklist to get the item IDs. Returns the issue's checklist "
        "after the deletion.",
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
    )
    async def issue_delete_checklist_item(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        checklist_item_id: IssueChecklistItemIDParam,
    ) -> list[ChecklistItem]:
        check_issue_access(settings, issue_id, write=True)

        return await ctx.request_context.lifespan_context.issues.issue_delete_checklist_item(
            issue_id,
            checklist_item_id,
            auth=get_yandex_auth(ctx),
        )
