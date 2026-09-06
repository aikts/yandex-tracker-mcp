from mcp.server.mcpserver import Context, MCPServer
from pydantic import BaseModel

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings


class YandexTrackerMCPConfigurationResponse(BaseModel):
    cloud_org_id: str | None
    org_id: str | None
    read_only: bool
    cache_enabled: bool
    entities_enabled: bool


def register_resources(settings: Settings, mcp: MCPServer[AppContext]) -> None:
    # A template rather than a static resource: a static `@mcp.resource()`
    # handler cannot receive `Context` in mcp 2.x, and the request is what
    # carries the per-call organization override (`?cloudOrgId=` / `?orgId=`
    # on the HTTP request, see `get_yandex_auth`). The query variables are
    # optional, so plain `tracker-mcp://configuration` still matches; the
    # resource is listed under `resources/templates/list`.
    @mcp.resource(
        "tracker-mcp://configuration{?cloudOrgId,orgId}",
        description="Retrieve configured Yandex Tracker MCP configuration.",
    )
    async def tracker_mcp_configuration(
        # Bare `Context` on purpose: template handlers go through
        # `pydantic.validate_call`, which re-validates a parametrized
        # `Context[...]` into a fresh instance detached from the request.
        ctx: Context,
        cloudOrgId: str | None = None,
        orgId: str | None = None,
    ) -> YandexTrackerMCPConfigurationResponse:
        auth = get_yandex_auth(ctx)

        return YandexTrackerMCPConfigurationResponse(
            cloud_org_id=cloudOrgId
            or auth.cloud_org_id
            or settings.tracker_cloud_org_id,
            org_id=orgId or auth.org_id or settings.tracker_org_id,
            read_only=settings.tracker_read_only,
            cache_enabled=settings.tools_cache_enabled,
            entities_enabled=settings.tracker_entities_enabled,
        )
