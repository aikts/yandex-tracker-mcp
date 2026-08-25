import json
from typing import Any

MAX_ERROR_BODY_LENGTH = 1000


class YandexTrackerError(Exception):
    pass


class IssueNotFound(YandexTrackerError):
    def __init__(self, issue_id: str):
        super().__init__(f"Issue with ID '{issue_id}' not found.")
        self.issue_id = issue_id


class QueueNotFound(YandexTrackerError):
    def __init__(self, queue_id: str):
        super().__init__(f"Queue with ID '{queue_id}' not found.")
        self.queue_id = queue_id


class IssueTemplateNotFound(YandexTrackerError):
    def __init__(self, template_id: str):
        super().__init__(f"Issue template with ID '{template_id}' not found.")
        self.template_id = template_id


class CommentTemplateNotFound(YandexTrackerError):
    def __init__(self, template_id: str):
        super().__init__(f"Comment template with ID '{template_id}' not found.")
        self.template_id = template_id


class IssueVersionConflict(YandexTrackerError):
    """Raised when an update is rejected because `version` is not current.

    Tracker bumps an issue's version on every change, including changes made by
    queue triggers and automation right after the issue is created, so a version
    read moments ago can already be stale.
    """

    def __init__(self, issue_id: str, version: int | None = None):
        expected = f" with version {version}" if version is not None else ""
        super().__init__(
            f"Editing conflict for issue '{issue_id}'{expected}: the issue was changed "
            f"in the meantime (queue triggers and automation change it too, so the "
            f"version returned by issue_create is often already outdated). "
            f"Re-read the issue with issue_get to get its current version and retry, "
            f"or omit the version parameter to update the latest version unconditionally."
        )
        self.issue_id = issue_id
        self.version = version


class TrackerAPIError(YandexTrackerError):
    """A non-2xx response from the Yandex Tracker API.

    Tracker explains *why* a request was rejected in the response body
    (`errorMessages` / `errors`), which is the only way to tell, for example,
    which field of an issue_create call was invalid. The body is therefore part
    of the raised error instead of being dropped by `raise_for_status()`.
    """

    def __init__(self, *, status: int, method: str, url: str, body: str):
        self.status = status
        self.method = method
        self.url = url
        self.body = body
        self.error_messages, self.errors = _parse_error_body(body)

        details: list[str] = list(self.error_messages)
        details.extend(f"{field}: {message}" for field, message in self.errors.items())
        if not details and body:
            details.append(body[:MAX_ERROR_BODY_LENGTH])

        message = f"Yandex Tracker API error {status} on {method} {url}"
        if details:
            message += ": " + "; ".join(details)
        super().__init__(message)


def _parse_error_body(body: str) -> tuple[list[str], dict[str, str]]:
    """Extract Tracker's `errorMessages` / `errors` from an error response body."""
    try:
        parsed: Any = json.loads(body)
    except ValueError:
        return [], {}

    if not isinstance(parsed, dict):
        return [], {}

    raw_messages = parsed.get("errorMessages")
    messages = [str(m) for m in raw_messages] if isinstance(raw_messages, list) else []

    raw_errors = parsed.get("errors")
    errors = (
        {str(k): str(v) for k, v in raw_errors.items()}
        if isinstance(raw_errors, dict)
        else {}
    )

    return messages, errors


class ChecklistItemNotFound(YandexTrackerError):
    """Raised when *_update_checklist is asked to edit an id that isn't in the
    entity's current checklist.

    The bulk-edit endpoint can only edit items that already exist - it has no
    way to add one - so an unknown id here means the caller wanted
    *_add_checklist_item instead.
    """

    def __init__(self, entity_id: str, checklist_item_id: str):
        super().__init__(
            f"Checklist item '{checklist_item_id}' was not found on entity "
            f"'{entity_id}'. *_update_checklist can only edit items that already "
            f"exist - use *_add_checklist_item to add a new one."
        )
        self.entity_id = entity_id
        self.checklist_item_id = checklist_item_id


class EntityLinksOnlyUpdate(YandexTrackerError):
    """Raised for an entity update that would only change links.

    Verified against the live API: Tracker answers 200 but ignores `links`
    unless the same request also changes the entity (a field value or a
    comment), so such a call would silently do nothing.
    """

    def __init__(self) -> None:
        super().__init__(
            "Yandex Tracker ignores `links` when the update changes nothing else: "
            "pass at least one field to change, or a `comment`, in the same call. "
            "Note that links are added, not replaced - sending a link that already "
            "exists fails, and links cannot be removed through this server."
        )


class AttachmentNotFound(YandexTrackerError):
    def __init__(self, issue_id: str, attachment_id: str, file_name: str):
        super().__init__(
            f"Attachment '{file_name}' (id={attachment_id}) "
            f"for issue '{issue_id}' not found."
        )
        self.issue_id = issue_id
        self.attachment_id = attachment_id
        self.file_name = file_name
