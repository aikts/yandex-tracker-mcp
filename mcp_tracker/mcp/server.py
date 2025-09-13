import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import yarl
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from pydantic import ValidationError
from starlette.routing import Route

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.stores.memory import InMemoryOAuthStore
from mcp_tracker.mcp.oauth.stores.redis import RedisOAuthStore
from mcp_tracker.mcp.params import (
    instructions,
)
from mcp_tracker.mcp.resources import register_resources
from mcp_tracker.mcp.tools import register_tools
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.custom.client import ServiceAccountSettings, TrackerClient
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol

try:
    settings = Settings()
except ValidationError as e:
    sys.stderr.write(str(e) + "\n")
    sys.exit(1)


@asynccontextmanager
async def tracker_lifespan(server: FastMCP[Any]) -> AsyncIterator[AppContext]:
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
        token_type=settings.oauth_token_type,
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


def create_mcp_server() -> FastMCP[Any]:
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

        scopes: list[str] | None = None
        if settings.oauth_use_scopes:
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
            use_scopes=settings.oauth_use_scopes,
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
register_resources(settings, mcp)
register_tools(settings, mcp)
