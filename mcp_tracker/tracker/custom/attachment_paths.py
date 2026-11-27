import re

from mcp_tracker.tracker.custom.errors import (
    AttachmentNotFound,
    InvalidAttachmentIssueKey,
)

ISSUE_KEY = re.compile(r"[A-Za-z0-9_]+-[0-9]+")
ATTACHMENT_ID = re.compile(r"[A-Za-z0-9_-]+")


def validate_attachment_issue_key(issue_id: str) -> None:
    if ISSUE_KEY.fullmatch(issue_id) is None:
        raise InvalidAttachmentIssueKey()


def attachment_collection_path(issue_id: str) -> str:
    validate_attachment_issue_key(issue_id)
    return f"v3/issues/{issue_id}/attachments"


def attachment_path(issue_id: str, attachment_id: str) -> str:
    collection = attachment_collection_path(issue_id)
    if ATTACHMENT_ID.fullmatch(attachment_id) is None:
        raise AttachmentNotFound(issue_id, attachment_id)
    return f"{collection}/{attachment_id}"
