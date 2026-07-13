import asyncio
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request

from mcp_tracker.tracker.custom.safe_identifiers import validate_safe_identifier
from mcp_tracker.tracker.proto.common import YandexAuth

T = TypeVar("T", bound=BaseModel)


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


def _mkdir_attachment_directory(directory: Path) -> None:
    if directory.exists() and directory.is_file():
        msg = f"save_directory is a file, expected directory: {directory}"
        raise ValueError(msg)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        msg = f"Failed to create save directory {directory}: {e}"
        raise ValueError(msg) from e


def _write_bytes_exclusive(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as file_obj:
            file_obj.write(data)
    except FileExistsError as e:
        msg = f"Attachment file already exists: {path}"
        raise ValueError(msg) from e
    except OSError as e:
        msg = f"Failed to write attachment file {path}: {e}"
        raise ValueError(msg) from e


async def resolve_issue_attachment_local_path(
    *,
    issue_id: str,
    attachment_id: str,
    file_name: str,
    save_directory: str,
    attachments_base_dir: str | Path,
) -> Path:
    """Resolve a sandbox-local path for a downloaded attachment.

    File name is deterministic: ``{issue_id}-{attachment_id}{suffix}``.
    If that path already exists, raises ``ValueError`` (no silent overwrite).
    """
    validate_safe_identifier(issue_id, field_name="issue_id")
    validate_safe_identifier(attachment_id, field_name="attachment_id")

    base_dir = Path(attachments_base_dir).resolve()
    directory = Path(save_directory).resolve()
    if not directory.is_relative_to(base_dir):
        msg = f"save_directory must be inside {base_dir}, got {directory}"
        raise ValueError(msg)

    await asyncio.to_thread(_mkdir_attachment_directory, directory)

    safe_name = Path(file_name).name
    local_path = directory / f"{issue_id}-{attachment_id}{Path(safe_name).suffix}"
    if local_path.exists():
        msg = f"Attachment file already exists: {local_path}"
        raise ValueError(msg)
    return local_path


async def save_issue_attachment_file(
    data: bytes,
    *,
    issue_id: str,
    attachment_id: str,
    file_name: str,
    save_directory: str,
    attachments_base_dir: str | Path,
) -> Path:
    local_path = await resolve_issue_attachment_local_path(
        issue_id=issue_id,
        attachment_id=attachment_id,
        file_name=file_name,
        save_directory=save_directory,
        attachments_base_dir=attachments_base_dir,
    )
    await asyncio.to_thread(_write_bytes_exclusive, local_path, data)
    return local_path
