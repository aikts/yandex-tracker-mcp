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


class TestAllowListsIgnoreCase:
    """Tracker's queue keys are upper-case; the env vars are written by hand.

    Comparing the two exactly made a mis-cased entry silently wrong instead of
    rejected - an allow-list of `dev` locked out `DEV-1` along with everything
    else, and a read-only list of `dev` left `DEV` writable.
    """

    @pytest.mark.parametrize("configured", ["ALLOWED", "allowed", "Allowed"])
    @pytest.mark.parametrize("requested", ["ALLOWED", "allowed", "Allowed"])
    def test_limit_queues_matches_whatever_the_case(
        self, configured: str, requested: str
    ) -> None:
        settings = create_test_settings(limit_queues=[configured])

        check_queue_access(settings, requested)
        check_issue_access(settings, f"{requested}-1")

    @pytest.mark.parametrize("configured", ["OTHER", "other"])
    def test_a_queue_outside_the_list_is_still_rejected(self, configured: str) -> None:
        settings = create_test_settings(limit_queues=[configured])

        with pytest.raises(TrackerError, match="not found or not allowed"):
            check_queue_access(settings, "ALLOWED")
        with pytest.raises(IssueNotFound):
            check_issue_access(settings, "ALLOWED-1")

    @pytest.mark.parametrize("configured", ["READONLY", "readonly", "ReadOnly"])
    @pytest.mark.parametrize("requested", ["READONLY", "readonly", "ReadOnly"])
    def test_read_only_queues_match_whatever_the_case(
        self, configured: str, requested: str
    ) -> None:
        settings = create_test_settings(read_only_queues=[configured])

        check_queue_access(settings, requested)
        with pytest.raises(TrackerError, match="read-only"):
            check_queue_access(settings, requested, write=True)
        with pytest.raises(TrackerError, match="read-only"):
            check_issue_access(settings, f"{requested}-1", write=True)


class TestSettingsParsing:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("READONLY", {"READONLY"}),
            ("A,B,C", {"A", "B", "C"}),
            (" A , B ,, C ", {"A", "B", "C"}),
            # The casing of the variable is settled here, once, rather than at
            # every comparison.
            ("readonly", {"READONLY"}),
            ("a, B ,c", {"A", "B", "C"}),
            # A list is what a programmatic caller passes; it is normalised the
            # same way, and duplicates that differ only in case collapse.
            (["A", "b"], {"A", "B"}),
            (["DEV", "dev"], {"DEV"}),
            (None, None),
        ],
    )
    def test_queue_keys_parsing(
        self, raw: str | list[str] | None, expected: set[str] | None
    ) -> None:
        parsed = Settings.decode_queue_keys(raw)
        assert parsed == expected

    def test_an_unsupported_type_is_rejected(self) -> None:
        with pytest.raises(TypeError):
            Settings.decode_queue_keys(42)
