import pytest

from mcp_tracker.tracker.custom.errors import IssueNotFound, YandexTrackerError


class TestYandexTrackerError:
    def test_is_exception(self):
        error = YandexTrackerError("test message")
        assert isinstance(error, Exception)

    def test_with_message(self):
        error = YandexTrackerError("Custom error message")
        assert str(error) == "Custom error message"

    def test_without_message(self):
        error = YandexTrackerError()
        assert str(error) == ""


class TestIssueNotFound:
    def test_inheritance(self):
        error = IssueNotFound("TEST-123")
        assert isinstance(error, YandexTrackerError)
        assert isinstance(error, Exception)

    def test_init_with_issue_id(self):
        issue_id = "PROJ-456"
        error = IssueNotFound(issue_id)

        assert error.issue_id == issue_id
        expected_message = "Issue with ID 'PROJ-456' not found."
        assert str(error) == expected_message

    def test_init_with_different_issue_formats(self):
        test_cases = [
            "SIMPLE-123",
            "COMPLEX_NAME-9999",
            "A-1",
            "VERY_LONG_PROJECT_NAME-12345",
        ]

        for issue_id in test_cases:
            error = IssueNotFound(issue_id)
            assert error.issue_id == issue_id
            assert f"Issue with ID '{issue_id}' not found." == str(error)

    def test_issue_id_attribute_accessible(self):
        issue_id = "ACCESS-TEST-789"
        error = IssueNotFound(issue_id)

        # Should be able to access the issue_id attribute
        assert hasattr(error, "issue_id")
        assert error.issue_id == issue_id

    def test_can_be_raised_and_caught(self):
        issue_id = "RAISE-TEST-001"

        with pytest.raises(IssueNotFound) as exc_info:
            raise IssueNotFound(issue_id)

        caught_error = exc_info.value
        assert caught_error.issue_id == issue_id
        assert str(caught_error) == f"Issue with ID '{issue_id}' not found."

    def test_can_be_caught_as_yandex_tracker_error(self):
        issue_id = "CATCH-TEST-002"

        with pytest.raises(YandexTrackerError) as exc_info:
            raise IssueNotFound(issue_id)

        caught_error = exc_info.value
        assert isinstance(caught_error, IssueNotFound)
        assert caught_error.issue_id == issue_id
