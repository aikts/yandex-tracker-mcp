"""Issue write MCP tools (conditionally registered based on read-only mode)."""

import datetime
from pathlib import Path
from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ClientCapabilities, ElicitationCapability, ToolAnnotations
from pydantic import BaseModel, Field, create_model

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.params import (
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
from mcp_tracker.mcp.utils import get_yandex_auth, resolve_issue_attachment_local_path
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.inputs import (
    IssuePriorityRef,
    IssueTypeRef,
)
from mcp_tracker.tracker.proto.types.issues import (
    DownloadedIssueAttachment,
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
        description="Create a new issue in a Yandex Tracker queue. "
        "Check the queue's issue templates first (`issue_templates_get_all` with `queue` set): "
        "there is no `template_id` parameter, so a template is applied by copying its "
        "`fieldTemplates` values and description into the parameters below instead of inventing "
        "a structure of your own. Copy them field by field rather than wholesale: `assignee` comes "
        "as a user object, while this tool takes a login or uid, and Tracker does not expand the "
        "UI macros a template may contain (`{{today}}` and friends arrive literally). "
        "Prefer the dedicated parameters below over the `fields` map: they are sent in the "
        "same format issue_update uses, so a value that works here works there too. "
        "Note that the returned issue's `version` can be outdated as soon as it is returned - "
        "queue triggers and automation run right after creation and bump it - so do not reuse it "
        "for a follow-up issue_update; re-read the issue with issue_get or omit `version`.",
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
                description="Additional fields to set during issue creation, for fields without a "
                "dedicated parameter above. "
                "Call `queue_get_fields` for the fields configured on the queue (schema.required=true "
                "marks the mandatory ones) and `get_global_fields` for the whole registry - system "
                "fields such as `parent` or `estimation` are settable but may be missing from the "
                "queue listing. "
                "Keys are Tracker field ids as those tools return them (camelCase, e.g. 'storyPoints'), "
                "which is also how they come back in issue responses. "
                "An entry here overrides the dedicated parameter of the same name. "
                "Values are sent to Tracker as-is: reference fields expect numeric IDs as numbers "
                "(or {'id': ...} objects), because a bare string may be resolved as a name."
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
        description="Update an existing Yandex Tracker issue. "
        "Only fields that are provided will be updated; omitted fields remain unchanged. "
        "Use queue_get_fields to discover available fields before updating. "
        "The `version` parameter is optional optimistic locking: pass it only when you have a "
        "version read moments ago (issue_get), and never the one returned by issue_create - "
        "queue triggers and automation bump the version right after creation, which makes the "
        "update fail with an editing conflict.",
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
                description="Issue version for optimistic locking; changes are only applied when it is "
                "the issue's current version, otherwise the call fails with an editing conflict. "
                "Read it with issue_get immediately before updating, and omit it when you just want the "
                "update to land on whatever the latest version is. The version returned by issue_create "
                "is not safe to use here: queue triggers and automation bump it right after creation."
            ),
        ] = None,
        fields: Annotated[
            dict[str, Any] | None,
            Field(
                description="Additional fields to update, for fields without a dedicated parameter above. "
                "Call `queue_get_fields` for the fields configured on the queue and `get_global_fields` "
                "for the whole registry - system fields such as `parent` or `estimation` are settable "
                "but may be missing from the queue listing. "
                "Keys are Tracker field ids as those tools return them (camelCase, e.g. 'storyPoints'), "
                "which is also how they come back in issue responses. "
                "An entry here overrides the dedicated parameter of the same name, which is how a field "
                "is cleared: pass null (e.g. {'assignee': null, 'parent': null}), since a dedicated "
                "parameter left unset simply is not sent. "
                "Values are sent to Tracker as-is: reference fields expect numeric IDs as numbers "
                "(or {'id': ...} objects), because a bare string may be resolved as a name."
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
        description="Add a comment to a Yandex Tracker issue. "
        "Check the queue's comment templates first (`comment_templates_get_all` with `queue` set): "
        "there is no `template_id` parameter, so a template is applied by copying its `template` "
        "text into `text` and its `summonees` / `maillistSummonees` into the parameters below "
        "instead of inventing wording of your own. "
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


def register_issue_attachment_download_tool(
    settings: Settings, mcp: FastMCP[Any]
) -> None:
    """Register issue attachment download tool (opt-in via settings)."""

    @mcp.tool(
        title="Download Issue Attachment",
        description=(
            "Download a Yandex Tracker issue attachment. "
            "Saved as {issue_id}-{attachment_id}{suffix}, where suffix is Path(file_name).suffix "
            "(e.g. archive.tar.gz → .gz). "
            "Returns issue_id, attachment_id, local_path, name, original_name, mime_type, and size."
        ),
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    async def issue_download_attachment(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        attachment_id: str,
        file_name: str,
        save_directory: Annotated[
            str,
            Field(
                description="Directory to save the downloaded file.",
            ),
        ],
    ) -> DownloadedIssueAttachment:
        check_issue_access(settings, issue_id)

        safe_file_name = Path(file_name).name
        local_path = resolve_issue_attachment_local_path(
            issue_id=issue_id,
            attachment_id=attachment_id,
            file_name=file_name,
            save_directory=save_directory,
            attachments_base_dir=settings.tracker_attachments_dir,
        )
        auth = get_yandex_auth(ctx)
        attachments = (
            await ctx.request_context.lifespan_context.issues.issue_get_attachments(
                issue_id,
                auth=auth,
            )
        )
        attachment = next((a for a in attachments if a.id == attachment_id), None)
        mime_type = attachment.mimetype if attachment else None

        size = (
            await ctx.request_context.lifespan_context.issues.issue_download_attachment(
                issue_id,
                attachment_id,
                safe_file_name,
                local_path,
                auth=auth,
            )
        )

        base_dir = Path(settings.tracker_attachments_dir).resolve()
        return DownloadedIssueAttachment(
            issue_id=issue_id,
            attachment_id=attachment_id,
            local_path=str(local_path.relative_to(base_dir)),
            name=local_path.name,
            original_name=safe_file_name,
            mime_type=mime_type,
            size=size,
        )
