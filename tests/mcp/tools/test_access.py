"""Unit tests for the access-control helpers in ``mcp/tools/_access.py``."""

import pytest

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.tools._access import (
    check_component_access,
    check_issue_access,
    check_queue_access,
    queue_checks_needed,
)
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import ComponentNotFound, IssueNotFound
from tests.mcp.conftest import create_test_settings
from tests.mcp.tools.conftest import component_in


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


class TestQueueChecksNeeded:
    """Whether a tool has to read an entity to learn its queue before acting."""

    @pytest.mark.parametrize("write", [False, True])
    def test_unrestricted_server_needs_none(self, write: bool) -> None:
        settings = create_test_settings()

        assert queue_checks_needed(settings, write=write) is False

    @pytest.mark.parametrize("write", [False, True])
    def test_limit_queues_needs_them_for_reads_and_writes(self, write: bool) -> None:
        settings = create_test_settings(limit_queues=["ALLOWED"])

        assert queue_checks_needed(settings, write=write) is True

    def test_read_only_queues_need_them_for_writes_only(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        assert queue_checks_needed(settings, write=False) is False
        assert queue_checks_needed(settings, write=True) is True


class TestCheckComponentAccess:
    """A component is checked through the queue it belongs to."""

    @pytest.mark.parametrize("queue_key", ["TEST", None])
    def test_unrestricted_server_allows_everything(self, queue_key: str | None) -> None:
        settings = create_test_settings()

        # Even a component without a queue: there is nothing to check it against.
        check_component_access(settings, component_in(queue_key))
        check_component_access(settings, component_in(queue_key), write=True)

    def test_allowed_queue_passes(self) -> None:
        settings = create_test_settings(limit_queues=["ALLOWED"])

        check_component_access(settings, component_in("ALLOWED"))
        check_component_access(settings, component_in("ALLOWED"), write=True)

    @pytest.mark.parametrize("write", [False, True])
    def test_queue_outside_the_allow_list_is_not_found(self, write: bool) -> None:
        """The key of a hidden queue must not be named back to the caller."""
        settings = create_test_settings(limit_queues=["ALLOWED"])

        with pytest.raises(ComponentNotFound) as excinfo:
            check_component_access(settings, component_in("OTHER"), write=write)

        assert excinfo.value.component_id == 856
        assert "OTHER" not in str(excinfo.value)

    def test_read_only_queue_allows_reads_and_rejects_writes(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        check_component_access(settings, component_in("READONLY"))
        with pytest.raises(TrackerError, match="read-only"):
            check_component_access(settings, component_in("READONLY"), write=True)

    def test_writable_queue_allows_writes(self) -> None:
        settings = create_test_settings(read_only_queues=["READONLY"])

        check_component_access(settings, component_in("TEST"), write=True)

    @pytest.mark.parametrize(
        ("limit_queues", "read_only_queues", "write"),
        [
            (["ALLOWED"], None, False),
            (["ALLOWED"], None, True),
            (None, ["READONLY"], True),
        ],
    )
    def test_component_without_a_queue_is_refused_under_a_restriction(
        self,
        limit_queues: list[str] | None,
        read_only_queues: list[str] | None,
        write: bool,
    ) -> None:
        """Its queue cannot be checked, so it is not let through."""
        settings = create_test_settings(
            limit_queues=limit_queues, read_only_queues=read_only_queues
        )

        with pytest.raises(TrackerError, match="names no queue"):
            check_component_access(settings, component_in(None), write=write)


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
        check_component_access(settings, component_in(requested))

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
        with pytest.raises(TrackerError, match="read-only"):
            check_component_access(settings, component_in(requested), write=True)


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
