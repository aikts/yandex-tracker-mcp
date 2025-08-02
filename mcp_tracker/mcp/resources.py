from typing import Any, cast

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings


class YandexTrackerMCPConfigurationResponse(BaseModel):
    cloud_org_id: str | None
    org_id: str | None
    read_only: bool
    cache_enabled: bool


def register_resources(settings: Settings, mcp: FastMCP[Any]):
    @mcp.resource(
        "tracker-mcp://configuration",
        description="Retrieve configured Yandex Tracker MCP configuration.",
    )
    async def tracker_mcp_configuration() -> YandexTrackerMCPConfigurationResponse:
        ctx = cast(Context[Any, AppContext, Request], mcp.get_context())
        auth = get_yandex_auth(ctx)

        return YandexTrackerMCPConfigurationResponse(
            cloud_org_id=auth.cloud_org_id or settings.tracker_cloud_org_id,
            org_id=auth.org_id or settings.tracker_org_id,
            read_only=settings.tracker_read_only,
            cache_enabled=settings.tools_cache_enabled,
        )
