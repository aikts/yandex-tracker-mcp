import uuid
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any, TypeVar, get_args

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp import Context
from pydantic import BaseModel
from starlette.requests import Request

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
        model_fields = type(item).model_fields
        extra = item.__pydantic_extra__
        # `model_fields_set` is mutated below, so iterate over a snapshot.
        for field in tuple(item.model_fields_set):
            if field in needed_fields:
                continue

            if extra is not None and field in extra:
                # Fields the API returned that the model does not declare
                # (`self`, `id`, `queue`, `boards`, the queue's own
                # `<queue-id>--<key>` fields) live in `__pydantic_extra__`,
                # which carries no `exclude_if=none_excluder`. Nulling one
                # leaves it in the response as an explicit `null`, so dropping
                # it is the only way to honour the field selection.
                del extra[field]
                item.__pydantic_fields_set__.discard(field)
                continue

            field_info = model_fields.get(field)
            # Skip fields whose declared type doesn't allow None (e.g. required
            # `id: int`) - nulling them would produce a response that violates
            # the tool's own output schema.
            if field_info is not None and type(None) not in get_args(
                field_info.annotation
            ):
                continue
            setattr(item, field, None)


def _mkdir_attachment_directory(directory: Path) -> None:
    if directory.is_file():
        msg = f"save path is a file, expected directory: {directory}"
        raise ValueError(msg)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        msg = f"Failed to create save directory {directory}: {e}"
        raise ValueError(msg) from e


def resolve_issue_attachment_local_path(
    *,
    original_name: str,
    attachments_base_dir: str | Path,
) -> Path:
    """Resolve a sandbox-local path for a downloaded attachment.

    Layout: ``{base}/{YYYY-MM-DD}/{random}{suffix}``. Suffix comes from the
    original Tracker name; the on-disk basename is a random hex id so the
    caller cannot pick a path. If that path already exists, raises
    ``ValueError`` (no silent overwrite). Bytes are written later by
    ``TrackerClient.issue_download_attachment``.
    """
    base_dir = Path(attachments_base_dir).resolve()
    directory = base_dir / date.today().isoformat()
    _mkdir_attachment_directory(directory)

    suffix = Path(Path(original_name).name).suffix
    local_path = directory / f"{uuid.uuid4().hex}{suffix}"
    if local_path.exists():
        msg = f"Attachment file already exists: {local_path}"
        raise ValueError(msg)
    return local_path
