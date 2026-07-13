import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request

from mcp_tracker.tracker.proto.common import YandexAuth

T = TypeVar("T", bound=BaseModel)
SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def get_yandex_auth(ctx: Context[Any, Any, Request]) -> YandexAuth:
    access_token = get_access_token()
    token = access_token.token if access_token else None

    # Passthrough mode: when MCP OAuth is disabled (no access_token from MCP auth
    # middleware), read the Yandex OAuth token directly from the Authorization
    # header. This enables use behind a reverse proxy that injects per-user
    # tokens (e.g. a gateway that resolves user identity and fetches their
    # stored OAuth token from a secret store).
    if token is None and ctx.request_context.request is not None:
        auth_header = ctx.request_context.request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip() or None

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


def set_non_needed_fields_null(data: Iterable[T], needed_fields: set[str]) -> None:
    for item in data:
        for field in item.model_fields_set:
            if field not in needed_fields:
                setattr(item, field, None)


def save_issue_attachment_file(
    data: bytes,
    *,
    issue_id: str,
    attachment_id: str,
    file_name: str,
    save_directory: str,
) -> Path:
    # Keep generated local file names predictable and path-safe.
    if not SAFE_IDENTIFIER_RE.fullmatch(issue_id):
        raise ValueError("issue_id contains unsafe characters")
    if not SAFE_IDENTIFIER_RE.fullmatch(attachment_id):
        raise ValueError("attachment_id contains unsafe characters")

    directory = Path(save_directory).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file_name).name
    local_path = directory / f"{issue_id}-{attachment_id}{Path(safe_name).suffix}"
    local_path.write_bytes(data)
    return local_path
