from typing import Any

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp import Context
from starlette.requests import Request

from mcp_tracker.tracker.proto.common import YandexAuth


def get_yandex_auth(ctx: Context[Any, Any, Request]) -> YandexAuth:
    access_token = get_access_token()
    token = access_token.token if access_token else None

    auth = YandexAuth(token=token)

    if ctx.request_context.request is not None:
        cloud_org_id = ctx.request_context.request.query_params.get("cloudOrgId")
        org_id = ctx.request_context.request.query_params.get("orgId")

        if cloud_org_id:
            cloud_org_id = cloud_org_id.strip()
            auth.cloud_org_id = cloud_org_id or None

        if org_id:
            org_id = org_id.strip()
            auth.org_id = org_id or None

    return auth
