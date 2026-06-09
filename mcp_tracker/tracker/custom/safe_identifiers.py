import re
from pathlib import Path
from urllib.parse import quote

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_safe_identifier(value: str, *, field_name: str) -> None:
    if not SAFE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} contains unsafe characters")


def build_attachment_download_path(
    issue_id: str, attachment_id: str, file_name: str
) -> str:
    validate_safe_identifier(issue_id, field_name="issue_id")
    validate_safe_identifier(attachment_id, field_name="attachment_id")
    safe_name = quote(Path(file_name).name, safe="")
    return f"v3/issues/{issue_id}/attachments/{attachment_id}/{safe_name}"
