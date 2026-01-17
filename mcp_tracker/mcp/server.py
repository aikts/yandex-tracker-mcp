import base64
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

import yarl
from mcp.server import FastMCP
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from starlette.routing import Route

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.oauth.provider import YandexOAuthAuthorizationServerProvider
from mcp_tracker.mcp.oauth.store import OAuthStore
from mcp_tracker.mcp.oauth.stores.memory import InMemoryOAuthStore
from mcp_tracker.mcp.oauth.stores.redis import RedisOAuthStore
from mcp_tracker.mcp.params import instructions
from mcp_tracker.mcp.resources import register_resources
from mcp_tracker.mcp.tools import register_all_tools
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.custom.client import ServiceAccountSettings, TrackerClient
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.users import UsersProtocol

# Type alias for lifespan
Lifespan = Callable[[FastMCP[Any]], AbstractAsyncContextManager[AppContext]]


def _parse_encryption_keys(keys_str: str | None) -> list[bytes] | None:
    """Parse comma-separated base64-encoded 32-byte encryption keys."""
    if not keys_str:
        return None

    keys: list[bytes] = []
    for i, key_b64 in enumerate(keys_str.split(","), start=1):
        if not (key_b64 := key_b64.strip()):
            continue
        try:
            key_bytes = base64.b64decode(key_b64)
        except Exception as e:
            raise ValueError(f"Encryption key {i} is not valid base64: {e}") from e
        if len(key_bytes) != 32:
            raise ValueError(
                f"Encryption key {i} must be 32 bytes, got {len(key_bytes)}"
            )
        keys.append(key_bytes)

    return keys if keys else None


def make_tracker_lifespan(settings: Settings) -> Lifespan:
    """Factory function to create tracker lifespan with given settings."""

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
        global_data: GlobalDataProtocol = tracker
        users: UsersProtocol = tracker
        if settings.tools_cache_enabled:
            cache_collection = make_cached_protocols(settings.cache_kwargs())
            queues = cache_collection.queues(queues)
            issues = cache_collection.issues(issues)
            global_data = cache_collection.global_data(global_data)
            users = cache_collection.users(users)

        try:
            await tracker.prepare()

            yield AppContext(
                queues=queues,
                issues=issues,
                fields=global_data,
                users=users,
            )
        finally:
            await tracker.close()

    return tracker_lifespan


def create_mcp_server(
    settings: Settings,
    lifespan: Lifespan | None = None,
) -> FastMCP[Any]:
    """Create MCP server with given settings and optional custom lifespan.

    Args:
        settings: Application settings
        lifespan: Optional custom lifespan. If None, uses make_tracker_lifespan(settings)
    """
    if lifespan is None:
        lifespan = make_tracker_lifespan(settings)

    auth_server_provider: YandexOAuthAuthorizationServerProvider | None = None
    auth_settings: AuthSettings | None = None

    if settings.oauth_enabled:
        assert settings.oauth_client_id, "OAuth client ID must be set."
        assert settings.oauth_client_secret, "OAuth client secret must be set."
        assert settings.mcp_server_public_url, "MCP server public url must be set."

        oauth_store: OAuthStore

        if settings.oauth_store == "memory":
            oauth_store = InMemoryOAuthStore()
        elif settings.oauth_store == "redis":
            encryption_keys = _parse_encryption_keys(settings.oauth_encryption_keys)
            if not encryption_keys:
                raise ValueError(
                    "OAUTH_ENCRYPTION_KEYS must be set when using Redis OAuth store. "
                    "Generate a key with: "
                    'python3 -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"'
                )

            oauth_store = RedisOAuthStore(
                endpoint=settings.redis_endpoint,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                pool_max_size=settings.redis_pool_max_size,
                encryption_keys=encryption_keys,
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
        lifespan=lifespan,
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

    register_resources(settings, server)
    register_all_tools(settings, server)

    return server
