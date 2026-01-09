from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.requests import Request
from thefuzz import process

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.params import (
    IssueID,
    IssueIDs,
    PageParam,
    PerPageParam,
    QueueID,
    UserID,
    YTQuery,
)
from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueFieldsEnum,
    IssueLink,
    IssueTransition,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import (
    Queue,
    QueueFieldsEnum,
    QueueVersion,
)
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User


def check_issue_id(settings: Settings, issue_id: str) -> None:
    queue, _ = issue_id.split("-")
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise IssueNotFound(issue_id)


def register_tools(settings: Settings, mcp: FastMCP[Any]):
    @mcp.tool(
        title="Get All Queues",
        description="Find all Yandex Tracker queues available to the user (queue is a project in some sense)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queues_get_all(
        ctx: Context[Any, AppContext, Request],
        fields: Annotated[
            list[QueueFieldsEnum] | None,
            Field(
                description="Fields to include in the response. In order to not pollute context window - "
                "select appropriate fields beforehand. Not specifying fields will return all available. "
                "Most of the time one needs key and name only.",
            ),
        ] = None,
        page: Annotated[
            int | None,
            Field(
                description="Page number to return, default is None which means to retrieve all pages. "
                "Specify page number to retrieve a specific page when context limit is reached.",
            ),
        ] = None,
        per_page: PerPageParam = 100,
    ) -> list[Queue]:
        result: list[Queue] = []

        find_all = False
        if page is None:
            page = 1
            find_all = True

        while find_all:
            queues = await ctx.request_context.lifespan_context.queues.queues_list(
                per_page=per_page,
                page=page,
                auth=get_yandex_auth(ctx),
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
            if find_all:
                page += 1

        if fields is not None:
            set_non_needed_fields_null(result, {f.name for f in fields})

        return result

    @mcp.tool(
        title="Get Queue Local Fields",
        description="Get local fields for a specific Yandex Tracker queue (queue-specific custom fields)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_local_fields(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[LocalField]:
        if (
            settings.tracker_limit_queues
            and queue_id not in settings.tracker_limit_queues
        ):
            raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

        fields = (
            await ctx.request_context.lifespan_context.queues.queues_get_local_fields(
                queue_id,
                auth=get_yandex_auth(ctx),
            )
        )
        return fields

    @mcp.tool(
        title="Get Queue Tags",
        description="Get all tags for a specific Yandex Tracker queue",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_tags(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[str]:
        if (
            settings.tracker_limit_queues
            and queue_id not in settings.tracker_limit_queues
        ):
            raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

        tags = await ctx.request_context.lifespan_context.queues.queues_get_tags(
            queue_id,
            auth=get_yandex_auth(ctx),
        )
        return tags

    @mcp.tool(
        title="Get Queue Versions",
        description="Get all versions for a specific Yandex Tracker queue",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_versions(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[QueueVersion]:
        if (
            settings.tracker_limit_queues
            and queue_id not in settings.tracker_limit_queues
        ):
            raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

        versions = (
            await ctx.request_context.lifespan_context.queues.queues_get_versions(
                queue_id,
                auth=get_yandex_auth(ctx),
            )
        )
        return versions

    @mcp.tool(
        title="Get Queue Fields",
        description="Get fields for a specific Yandex Tracker queue. "
        "Returns list of fields that can be used when creating issues in this queue. "
        "The schema.required property indicates whether a field is mandatory. "
        "Use this to find available and required fields before creating an issue with issue_create tool.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def queue_get_fields(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[GlobalField]:
        if (
            settings.tracker_limit_queues
            and queue_id not in settings.tracker_limit_queues
        ):
            raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

        fields = await ctx.request_context.lifespan_context.queues.queues_get_fields(
            queue_id,
            auth=get_yandex_auth(ctx),
        )
        return fields

    @mcp.tool(
        title="Get Queue Resolutions",
        description="Get resolutions available in a specific Yandex Tracker queue. "
        "Returns list of resolutions that can be used when closing issues in this queue. "
        "Use this to find valid resolution IDs for the issue_close tool.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_queue_resolutions(
        ctx: Context[Any, AppContext],
        queue_id: QueueID,
    ) -> list[Resolution]:
        if (
            settings.tracker_limit_queues
            and queue_id not in settings.tracker_limit_queues
        ):
            raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

        queue = await ctx.request_context.lifespan_context.queues.queue_get(
            queue_id,
            expand=["issueTypesConfig"],
            auth=get_yandex_auth(ctx),
        )

        if queue.issueTypesConfig:
            for conf in queue.issueTypesConfig:
                if conf.resolutions is not None:
                    return conf.resolutions

        return []

    @mcp.tool(
        title="Get Global Fields",
        description="Get all global fields available in Yandex Tracker that can be used in issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_global_fields(
        ctx: Context[Any, AppContext],
    ) -> list[GlobalField]:
        fields = await ctx.request_context.lifespan_context.fields.get_global_fields(
            auth=get_yandex_auth(ctx),
        )
        return fields

    @mcp.tool(
        title="Get Statuses",
        description="Get all statuses available in Yandex Tracker that can be used in issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_statuses(
        ctx: Context[Any, AppContext],
    ) -> list[Status]:
        statuses = await ctx.request_context.lifespan_context.fields.get_statuses(
            auth=get_yandex_auth(ctx),
        )
        return statuses

    @mcp.tool(
        title="Get Issue Types",
        description="Get all issue types available in Yandex Tracker that can be used when creating or updating issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_issue_types(
        ctx: Context[Any, AppContext],
    ) -> list[IssueType]:
        issue_types = await ctx.request_context.lifespan_context.fields.get_issue_types(
            auth=get_yandex_auth(ctx),
        )
        return issue_types

    @mcp.tool(
        title="Get Priorities",
        description="Get all priorities available in Yandex Tracker that can be used in issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_priorities(
        ctx: Context[Any, AppContext],
    ) -> list[Priority]:
        priorities = await ctx.request_context.lifespan_context.fields.get_priorities(
            auth=get_yandex_auth(ctx),
        )
        return priorities

    @mcp.tool(
        title="Get Resolutions",
        description="Get all resolutions available in Yandex Tracker that can be used when closing issues",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def get_resolutions(
        ctx: Context[Any, AppContext],
    ) -> list[Resolution]:
        resolutions = await ctx.request_context.lifespan_context.fields.get_resolutions(
            auth=get_yandex_auth(ctx),
        )
        return resolutions

    @mcp.tool(
        title="Get Issue URL",
        description="Get a Yandex Tracker issue url by its id",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_get_url(
        issue_id: IssueID,
    ) -> str:
        return f"https://tracker.yandex.ru/{issue_id}"

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
        check_issue_id(settings, issue_id)

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
        check_issue_id(settings, issue_id)

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
        check_issue_id(settings, issue_id)

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
            check_issue_id(settings, issue_id)

        result: dict[str, Any] = {}
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
        check_issue_id(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_attachments(
            issue_id,
            auth=get_yandex_auth(ctx),
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
        check_issue_id(settings, issue_id)

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
        check_issue_id(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_transitions(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

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
        check_issue_id(settings, issue_id)

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
        "IMPORTANT: You MUST first call get_queue_resolutions to retrieve available resolutions in the queue of this issue "
        "and pass a valid resolution_id. "
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
        check_issue_id(settings, issue_id)

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
                "IMPORTANT: Before creating an issue, you MUST call `queue_get_fields` to get available queue fields "
                "and `queue_get_local_fields` to get queue-specific custom fields. "
                "Fields with schema.required=true are mandatory and must be provided. "
                "Use the field's `id` property as the key in this map (e.g., {'fieldId': 'value'})."
            ),
        ] = None,
    ) -> Issue:
        # Check queue restrictions if enabled
        if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
            raise TrackerError(f"Access to queue '{queue}' is not allowed")

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
        title="Get All Users",
        description="Get information about user accounts registered in the organization",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def users_get_all(
        ctx: Context[Any, AppContext],
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> list[User]:
        users = await ctx.request_context.lifespan_context.users.users_list(
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )
        return users

    @mcp.tool(
        title="Search Users",
        description="Search user based on login, email or real name (first or last name, or both). "
        "Returns either single user or multiple users if several match the query or an empty list "
        "if no users matched.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def users_search(
        ctx: Context[Any, AppContext],
        login_or_email_or_name: Annotated[
            str, Field(description="User login, email or real name to search for")
        ],
    ) -> list[User]:
        per_page = 100
        page = 1

        login_or_email_or_name = login_or_email_or_name.strip().lower()

        all_users: list[User] = []

        while True:
            batch = await ctx.request_context.lifespan_context.users.users_list(
                per_page=per_page,
                page=page,
                auth=get_yandex_auth(ctx),
            )

            if not batch:
                break

            for user in batch:
                if user.login and login_or_email_or_name == user.login.strip().lower():
                    return [user]

                if user.email and login_or_email_or_name == user.email.strip().lower():
                    return [user]

            all_users.extend(batch)
            page += 1

        names = {
            idx: f"{u.first_name} {u.last_name}" for idx, u in enumerate(all_users)
        }
        results = process.extractBests(
            login_or_email_or_name, names, score_cutoff=80, limit=3
        )
        matched_users = [all_users[idx] for name, score, idx in results]
        return matched_users

    @mcp.tool(
        title="Get User",
        description="Get information about a specific user by login or UID",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def user_get(
        ctx: Context[Any, AppContext],
        user_id: UserID,
    ) -> User:
        user = await ctx.request_context.lifespan_context.users.user_get(
            user_id,
            auth=get_yandex_auth(ctx),
        )
        if user is None:
            raise TrackerError(f"User `{user_id}` not found.")

        return user

    @mcp.tool(
        title="Get Current User",
        description="Get information about the current authenticated user",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def user_get_current(
        ctx: Context[Any, AppContext],
    ) -> User:
        user = await ctx.request_context.lifespan_context.users.user_get_current(
            auth=get_yandex_auth(ctx),
        )
        return user
