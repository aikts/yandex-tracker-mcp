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


class BoardNotFound(YandexTrackerError):
    def __init__(self, board_id: int):
        super().__init__(f"Board with ID '{board_id}' not found.")
        self.board_id = board_id


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


class TrackerAPITimeout(YandexTrackerError):
    """A request to the Yandex Tracker API ran out of its time budget.

    Worth a class of its own only because the alternative is unreadable:
    `str(TimeoutError())` is the empty string, so a timeout reaches the caller
    as `Error executing tool <name>:` with nothing after the colon and no hint
    that time, rather than the request, was the problem.
    """

    def __init__(self, *, method: str, url: str, timeout: float):
        self.method = method
        self.url = url
        self.timeout = timeout
        super().__init__(
            f"Yandex Tracker API request {method} {url} timed out after "
            f"{timeout:g}s. Raise TRACKER_API_TIMEOUT if this endpoint is "
            f"slow for this organization."
        )


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
    """Raised when a checklist edit names an id that isn't in the current
    checklist of the issue or entity.

    The edit endpoints can only change items that already exist - they have no
    way to add one - so an unknown id here means the caller wanted an
    *_add_checklist_item(s) tool instead.

    `ambiguous` is set where the id came back as a 404 from an item-scoped path
    (`.../checklistItems/{itemId}`), which Tracker answers the same way for an
    unknown issue as for an unknown item: the message then names both causes
    instead of asserting the one it cannot tell apart. Where the checklist was
    read first, the entity is known to exist and the message stays specific.
    """

    def __init__(
        self, entity_id: str, checklist_item_id: str, *, ambiguous: bool = False
    ):
        if ambiguous:
            message = (
                f"Checklist item '{checklist_item_id}' was not found on "
                f"'{entity_id}'. Tracker answers the same 404 when the issue "
                f"itself does not exist, so check both the id of the issue and "
                f"the id of the item - issue_get_checklist lists the current ones."
            )
        else:
            message = (
                f"Checklist item '{checklist_item_id}' was not found on "
                f"'{entity_id}'. Only items that already exist can be edited - "
                f"use an *_add_checklist_item(s) tool to add a new one."
            )
        super().__init__(message)
        self.entity_id = entity_id
        self.checklist_item_id = checklist_item_id
        self.ambiguous = ambiguous


class ChecklistBatchPartiallyAdded(YandexTrackerError):
    """Raised when a batch of checklist items fails partway through.

    Tracker takes one item per request, so a batch is several requests and the
    ones that already succeeded are not rolled back. A bare error would leave
    the caller unable to tell how much of the batch landed, and a naive retry
    would duplicate those items.
    """

    def __init__(self, issue_id: str, added: int, total: int, cause: Exception):
        super().__init__(
            f"Added {added} of {total} checklist items to '{issue_id}' before the "
            f"request failed: {cause}. The items already added were kept - read the "
            f"checklist with issue_get_checklist and retry only what is missing, "
            f"or the successful ones will be duplicated."
        )
        self.issue_id = issue_id
        self.added = added
        self.total = total
        self.cause = cause


class ChecklistItemEmptyUpdate(YandexTrackerError):
    """Raised for a checklist item update that would change nothing.

    Verified against the live API: Tracker answers an empty PATCH body with 200
    and leaves the item untouched, so such a call is a silent no-op round-trip.
    It is refused here rather than reported back as a success.
    """

    def __init__(self) -> None:
        super().__init__(
            "A checklist item update must change something: pass at least one of "
            "`text`, `checked`, `assignee`, `deadline`, `clear_assignee` or "
            "`clear_deadline`. An omitted field keeps its current value; use the "
            "`clear_*` flags to remove one."
        )


class ChecklistItemClearConflict(YandexTrackerError):
    """Raised when an update both sets and clears the same checklist item field."""

    def __init__(self, field: str) -> None:
        super().__init__(
            f"`{field}` and `clear_{field}` cannot be passed together: pass "
            f"`{field}` to set a new value, or `clear_{field}` to remove the "
            f"current one."
        )


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
