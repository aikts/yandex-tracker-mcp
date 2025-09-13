from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
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
from mcp_tracker.mcp.utils import get_yandex_auth
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
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User


def check_issue_id(settings: Settings, issue_id: str) -> None:
    queue, _ = issue_id.split("-")
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise IssueNotFound(issue_id)


def register_tools(settings: Settings, mcp: FastMCP[Any]):
    @mcp.tool(
        description="Find all Yandex Tracker queues available to the user (queue is a project in some sense)"
    )
    async def queues_get_all(
        ctx: Context[Any, AppContext, Request],
    ) -> list[Queue]:
        result: list[Queue] = []
        per_page = 100
        page = 1

        while True:
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
            page += 1

        return result

    @mcp.tool(
        description="Get local fields for a specific Yandex Tracker queue (queue-specific custom fields)"
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

    @mcp.tool(description="Get all tags for a specific Yandex Tracker queue")
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

    @mcp.tool(description="Get all versions for a specific Yandex Tracker queue")
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
        description="Get all global fields available in Yandex Tracker that can be used in issues"
    )
    async def get_global_fields(
        ctx: Context[Any, AppContext],
    ) -> list[GlobalField]:
        fields = await ctx.request_context.lifespan_context.fields.get_global_fields(
            auth=get_yandex_auth(ctx),
        )
        return fields

    @mcp.tool(
        description="Get all statuses available in Yandex Tracker that can be used in issues"
    )
    async def get_statuses(
        ctx: Context[Any, AppContext],
    ) -> list[Status]:
        statuses = await ctx.request_context.lifespan_context.fields.get_statuses(
            auth=get_yandex_auth(ctx),
        )
        return statuses

    @mcp.tool(
        description="Get all issue types available in Yandex Tracker that can be used when creating or updating issues"
    )
    async def get_issue_types(
        ctx: Context[Any, AppContext],
    ) -> list[IssueType]:
        issue_types = await ctx.request_context.lifespan_context.fields.get_issue_types(
            auth=get_yandex_auth(ctx),
        )
        return issue_types

    @mcp.tool(
        description="Get all priorities available in Yandex Tracker that can be used in issues"
    )
    async def get_priorities(
        ctx: Context[Any, AppContext],
    ) -> list[Priority]:
        priorities = await ctx.request_context.lifespan_context.fields.get_priorities(
            auth=get_yandex_auth(ctx),
        )
        return priorities

    @mcp.tool(description="Get a Yandex Tracker issue url by its id")
    async def issue_get_url(
        issue_id: IssueID,
    ) -> str:
        return f"https://tracker.yandex.ru/{issue_id}"

    @mcp.tool(description="Get a Yandex Tracker issue by its id")
    async def issue_get(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
        include_description: Annotated[
            bool,
            Field(
                description="Whether to include issue description in the issues result. It can be large, so use only when needed.",
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

    @mcp.tool(description="Get comments of a Yandex Tracker issue by its id")
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
        description="Get a Yandex Tracker issue related links to other issues by its id"
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

    @mcp.tool(description="Find Yandex Tracker issues by queue and/or created date")
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
                description="Fields to include in the response. In order to not pollute context window - select appropriate fields beforehand. Not specifying fields will return all available."
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
            fields_set = {f.name for f in fields}

            for issue in issues:
                for field in issue.model_fields_set:
                    if field not in fields_set:
                        setattr(issue, field, None)

        return issues

    @mcp.tool(description="Get the count of Yandex Tracker issues matching a query")
    async def issues_count(
        ctx: Context[Any, AppContext],
        query: YTQuery,
    ) -> int:
        return await ctx.request_context.lifespan_context.issues.issues_count(
            query,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(description="Get worklogs of a Yandex Tracker issue by its id")
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

    @mcp.tool(description="Get attachments of a Yandex Tracker issue by its id")
    async def issue_get_attachments(
        ctx: Context[Any, AppContext],
        issue_id: IssueID,
    ) -> list[IssueAttachment]:
        check_issue_id(settings, issue_id)

        return await ctx.request_context.lifespan_context.issues.issue_get_attachments(
            issue_id,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(description="Get checklist items of a Yandex Tracker issue by its id")
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
        description="Get information about user accounts registered in the organization"
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
        description="Search user based on login, email or real name (first or last name, or both). Returns either single user or multiple users if several match the query or an empty list if no users matched."
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

    @mcp.tool(description="Get information about a specific user by login or UID")
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

    @mcp.tool(description="Get information about the current authenticated user")
    async def user_get_current(
        ctx: Context[Any, AppContext],
    ) -> User:
        user = await ctx.request_context.lifespan_context.users.user_get_current(
            auth=get_yandex_auth(ctx),
        )
        return user
