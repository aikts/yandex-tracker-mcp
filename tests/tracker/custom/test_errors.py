import pytest

from mcp_tracker.tracker.custom.errors import (
    AttachmentNotFound,
    IssueNotFound,
    YandexTrackerError,
)


class TestIssueNotFound:
    def test_can_be_caught_as_yandex_tracker_error(self):
        issue_id = "CATCH-TEST-002"

        with pytest.raises(YandexTrackerError) as exc_info:
            raise IssueNotFound(issue_id)

        caught_error = exc_info.value
        assert isinstance(caught_error, IssueNotFound)
        assert caught_error.issue_id == issue_id


class TestAttachmentNotFound:
    def test_can_be_caught_as_yandex_tracker_error(self) -> None:
        issue_id = "CATCH-TEST-003"
        attachment_id = "att-1"
        file_name = "doc.pdf"

        with pytest.raises(YandexTrackerError) as exc_info:
            raise AttachmentNotFound(issue_id, attachment_id, file_name)

        caught_error = exc_info.value
        assert isinstance(caught_error, AttachmentNotFound)
        assert caught_error.issue_id == issue_id
        assert caught_error.attachment_id == attachment_id
        assert caught_error.file_name == file_name
