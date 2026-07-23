"""Unit tests for the access-control helpers in ``mcp/tools/_access.py``."""

import pytest

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.tools._access import check_issue_access, check_queue_access
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import IssueNotFound
from tests.mcp.conftest import create_test_settings


class TestCheckIssueAccess:
    def test_no_restrictions_allows_read_and_write(self) -> None:
        settings = create_test_settings()

        # Should not raise for either read or write.
        check_issue_access(settings, "TEST-1")
        check_issue_access(settings, "TEST-1", write=True)

    def test_read_only_queue_allows_reads(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        # Read access to a read-only queue is permitted.
        check_issue_access(settings, "READONLY-1")

    def test_read_only_queue_rejects_writes(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        with pytest.raises(TrackerError, match="read-only"):
            check_issue_access(settings, "READONLY-1", write=True)

    def test_writable_queue_allows_writes(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        # A queue not in the read-only list stays writable.
        check_issue_access(settings, "TEST-1", write=True)

    def test_limit_queues_takes_precedence(self) -> None:
        settings = create_test_settings(
            limit_queues=["ALLOWED"], read_only_queues=["READONLY"]
        )

        # A queue outside the allow-list is not found, even for reads.
        with pytest.raises(IssueNotFound):
            check_issue_access(settings, "OTHER-1")

    def test_limit_and_read_only_combined(self) -> None:
        settings = create_test_settings(
            limit_queues=["ALLOWED", "READONLY"], read_only_queues=["READONLY"]
        )

        # Allowed + writable queue: read and write both fine.
        check_issue_access(settings, "ALLOWED-1", write=True)
        # Allowed but read-only queue: reads fine, writes rejected.
        check_issue_access(settings, "READONLY-1")
        with pytest.raises(TrackerError, match="read-only"):
            check_issue_access(settings, "READONLY-1", write=True)


class TestCheckQueueAccess:
    def test_no_restrictions_allows_read_and_write(self) -> None:
        settings = create_test_settings()

        check_queue_access(settings, "TEST")
        check_queue_access(settings, "TEST", write=True)

    def test_read_only_queue_allows_reads(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        check_queue_access(settings, "READONLY")

    def test_read_only_queue_rejects_writes(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        with pytest.raises(TrackerError, match="read-only"):
            check_queue_access(settings, "READONLY", write=True)

    def test_writable_queue_allows_writes(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        check_queue_access(settings, "TEST", write=True)

    def test_not_allowed_queue_rejected(self) -> None:
        settings = create_test_settings(limit_queues=["ALLOWED"])

        with pytest.raises(TrackerError, match="not found or not allowed"):
            check_queue_access(settings, "OTHER")


class TestSettingsParsing:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("READONLY", ["READONLY"]),
            ("A,B,C", ["A", "B", "C"]),
            (" A , B ,, C ", ["A", "B", "C"]),
            (None, None),
        ],
    )
    def test_read_only_queues_parsing(
        self, raw: str | None, expected: list[str] | None
    ) -> None:
        parsed = Settings.decode_numbers(raw)
        assert parsed == expected
