import pytest

from mcp_tracker.tracker.custom.errors import IssueNotFound, YandexTrackerError


class TestIssueNotFound:
    @pytest.mark.parametrize(
        "issue_id",
        [
            "SIMPLE-123",
            "COMPLEX_NAME-9999",
            "A-1",
            "VERY_LONG_PROJECT_NAME-12345",
        ],
    )
    def test_init_with_different_issue_formats(self, issue_id: str) -> None:
        error = IssueNotFound(issue_id)
        assert error.issue_id == issue_id
        assert f"Issue with ID '{issue_id}' not found." == str(error)

    def test_can_be_caught_as_yandex_tracker_error(self):
        issue_id = "CATCH-TEST-002"

        with pytest.raises(YandexTrackerError) as exc_info:
            raise IssueNotFound(issue_id)

        caught_error = exc_info.value
        assert isinstance(caught_error, IssueNotFound)
        assert caught_error.issue_id == issue_id
