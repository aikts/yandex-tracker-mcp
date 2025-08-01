import sys
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator

import yarl
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp import Context
from pydantic import Field, ValidationError
from starlette.requests import Request
from starlette.routing import Route

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.stores.memory import InMemoryOAuthStore
from mcp_tracker.mcp.oauth.stores.redis import RedisOAuthStore
from mcp_tracker.mcp.params import (
    IssueID,
    IssueIDs,
    QueueID,
    UserID,
    YTQuery,
    instructions,
)
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.custom.client import ServiceAccountSettings, TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User
from mcp_tracker.tracker.proto.users import UsersProtocol

try:
    settings = Settings()
except ValidationError as e:
    sys.stderr.write(str(e) + "\n")
    sys.exit(1)


@asynccontextmanager
async def tracker_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    service_account_settings: ServiceAccountSettings | None = None
    if (
        settings.tracker_sa_key_id
        and settings.tracker_sa_service_account_id
        and settings.tracker_sa_private_key
    ):
        service_account_settings = ServiceAccountSettings(
            key_id=settings.tracker_sa_key_id,
            service_account_id=settings.tracker_sa_service_account_id,
            private_key=settings.tracker_sa_private_key,
        )

    tracker = TrackerClient(
        base_url=settings.tracker_api_base_url,
        token=settings.tracker_token,
        iam_token=settings.tracker_iam_token,
        service_account=service_account_settings,
        cloud_org_id=settings.tracker_cloud_org_id,
        org_id=settings.tracker_org_id,
    )

    queues: QueuesProtocol = tracker
    issues: IssueProtocol = tracker
    fields: GlobalDataProtocol = tracker
    users: UsersProtocol = tracker
    if settings.tools_cache_enabled:
        queues_wrap, issues_wrap, fields_wrap, users_wrap = make_cached_protocols(
            settings.cache_kwargs()
        )
        queues = queues_wrap(queues)
        issues = issues_wrap(issues)
        fields = fields_wrap(fields)
        users = users_wrap(users)

    try:
        await tracker.prepare()

        yield AppContext(
            queues=queues,
            issues=issues,
            fields=fields,
            users=users,
        )
    finally:
        await tracker.close()


def create_mcp_server() -> FastMCP:
    auth_server_provider: YandexOAuthAuthorizationServerProvider | None = None
    auth_settings: AuthSettings | None = None

    if settings.oauth_enabled:
        assert settings.oauth_client_id, "OAuth client ID must be set."
        assert settings.oauth_client_secret, "OAuth client secret must be set."

        oauth_store: OAuthStore
        if settings.oauth_store == "memory":
            oauth_store = InMemoryOAuthStore()
        elif settings.oauth_store == "redis":
            oauth_store = RedisOAuthStore(
                endpoint=settings.redis_endpoint,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                pool_max_size=settings.redis_pool_max_size,
            )
        else:
            raise ValueError(
                f"Unsupported OAuth store: {settings.oauth_store}. "
                "Supported values are 'memory' and 'redis'."
            )

        if settings.tracker_read_only:
            scopes = ["tracker:read"]
        else:
            scopes = ["tracker:read", "tracker:write"]

        auth_server_provider = YandexOAuthAuthorizationServerProvider(
            client_id=settings.oauth_client_id,
            client_secret=settings.oauth_client_secret,
            server_url=yarl.URL(str(settings.mcp_server_public_url)),
            yandex_oauth_issuer=yarl.URL(str(settings.oauth_server_url)),
            store=oauth_store,
            scopes=scopes,
        )

        auth_settings = AuthSettings(
            issuer_url=settings.mcp_server_public_url,
            required_scopes=scopes,
            resource_server_url=settings.mcp_server_public_url,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=scopes,
                default_scopes=scopes,
            ),
        )

    server = FastMCP(
        name="Yandex Tracker MCP Server",
        instructions=instructions,
        host=settings.host,
        port=settings.port,
        lifespan=tracker_lifespan,
        auth_server_provider=auth_server_provider,
        stateless_http=True,
        json_response=True,
        auth=auth_settings,
    )

    if auth_server_provider is not None:
        server._custom_starlette_routes.append(
            Route(
                path="/oauth/yandex/callback",
                endpoint=auth_server_provider.handle_yandex_callback,
                methods=["GET"],
                name="oauth_yandex_callback",
            )
        )

    return server


mcp = create_mcp_server()


def check_issue_id(issue_id: str) -> None:
    queue, _ = issue_id.split("-")
    if settings.tracker_limit_queues and queue not in settings.tracker_limit_queues:
        raise IssueNotFound(issue_id)


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
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

    fields = await ctx.request_context.lifespan_context.queues.queues_get_local_fields(
        queue_id,
        auth=get_yandex_auth(ctx),
    )
    return fields


@mcp.tool(description="Get all tags for a specific Yandex Tracker queue")
async def queue_get_tags(
    ctx: Context[Any, AppContext],
    queue_id: QueueID,
) -> list[str]:
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
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
    if settings.tracker_limit_queues and queue_id not in settings.tracker_limit_queues:
        raise TrackerError(f"Queue `{queue_id}` not found or not allowed.")

    versions = await ctx.request_context.lifespan_context.queues.queues_get_versions(
        queue_id,
        auth=get_yandex_auth(ctx),
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
    check_issue_id(issue_id)

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
    check_issue_id(issue_id)

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
    check_issue_id(issue_id)

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
    page: Annotated[
        int,
        Field(
            description="Page number to return, default is 1",
        ),
    ] = 1,
) -> list[Issue]:
    per_page = 500

    issues = await ctx.request_context.lifespan_context.issues.issues_find(
        query=query,
        per_page=per_page,
        page=page,
        auth=get_yandex_auth(ctx),
    )

    if not include_description:
        for issue in issues:
            issue.description = None  # Clear description to save context

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
        check_issue_id(issue_id)

    result: dict[str, Any] = {}
    for issue_id in issue_ids:
        worklogs = await ctx.request_context.lifespan_context.issues.issue_get_worklogs(
            issue_id,
            auth=get_yandex_auth(ctx),
        )
        result[issue_id] = worklogs or []

    return result


@mcp.tool(description="Get attachments of a Yandex Tracker issue by its id")
async def issue_get_attachments(
    ctx: Context[Any, AppContext],
    issue_id: IssueID,
) -> list[IssueAttachment]:
    check_issue_id(issue_id)

    return await ctx.request_context.lifespan_context.issues.issue_get_attachments(
        issue_id,
        auth=get_yandex_auth(ctx),
    )


@mcp.tool(description="Get checklist items of a Yandex Tracker issue by its id")
async def issue_get_checklist(
    ctx: Context[Any, AppContext],
    issue_id: IssueID,
) -> list[ChecklistItem]:
    check_issue_id(issue_id)

    return await ctx.request_context.lifespan_context.issues.issue_get_checklist(
        issue_id,
        auth=get_yandex_auth(ctx),
    )


@mcp.tool(
    description="Get information about user accounts registered in the organization"
)
async def users_get_all(
    ctx: Context[Any, AppContext],
    per_page: Annotated[
        int,
        Field(
            description="Number of users per page (default: 50)",
            ge=1,
        ),
    ] = 50,
    page: Annotated[
        int,
        Field(
            description="Page number to return (default: 1)",
            ge=1,
        ),
    ] = 1,
) -> list[User]:
    users = await ctx.request_context.lifespan_context.users.users_list(
        per_page=per_page,
        page=page,
        auth=get_yandex_auth(ctx),
    )
    return users


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
