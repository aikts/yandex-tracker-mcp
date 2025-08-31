import pytest

from mcp_tracker.tracker.custom.errors import IssueNotFound, YandexTrackerError


class TestIssueNotFound:
    def test_can_be_caught_as_yandex_tracker_error(self):
        issue_id = "CATCH-TEST-002"

        with pytest.raises(YandexTrackerError) as exc_info:
            raise IssueNotFound(issue_id)

        caught_error = exc_info.value
        assert isinstance(caught_error, IssueNotFound)
        assert caught_error.issue_id == issue_id
