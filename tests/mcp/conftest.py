"""Shared fixtures for MCP server testing."""

from unittest.mock import AsyncMock

import pytest

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import Issue
from mcp_tracker.tracker.proto.types.queues import Queue
from mcp_tracker.tracker.proto.types.users import User


class MockQueuesProtocol:
    """Mock implementation of QueuesProtocol for testing."""

    def __init__(self):
        self.queues_list = AsyncMock()
        self.queues_get_local_fields = AsyncMock()
        self.queues_get_tags = AsyncMock()
        self.queues_get_versions = AsyncMock()


class MockIssueProtocol:
    """Mock implementation of IssueProtocol for testing."""

    def __init__(self):
        self.issue_get = AsyncMock()
        self.issue_get_comments = AsyncMock()
        self.issues_get_links = AsyncMock()
        self.issues_find = AsyncMock()
        self.issues_count = AsyncMock()
        self.issue_get_worklogs = AsyncMock()
        self.issue_get_attachments = AsyncMock()
        self.issue_get_checklist = AsyncMock()


class MockGlobalDataProtocol:
    """Mock implementation of GlobalDataProtocol for testing."""

    def __init__(self):
        self.get_global_fields = AsyncMock()
        self.get_statuses = AsyncMock()
        self.get_issue_types = AsyncMock()
        self.get_priorities = AsyncMock()


class MockUsersProtocol:
    """Mock implementation of UsersProtocol for testing."""

    def __init__(self):
        self.users_list = AsyncMock()
        self.user_get = AsyncMock()
        self.user_get_current = AsyncMock()


@pytest.fixture
def mock_queues_protocol():
    """Provides a mock QueuesProtocol instance."""
    return MockQueuesProtocol()


@pytest.fixture
def mock_issues_protocol():
    """Provides a mock IssueProtocol instance."""
    return MockIssueProtocol()


@pytest.fixture
def mock_global_data_protocol():
    """Provides a mock GlobalDataProtocol instance."""
    return MockGlobalDataProtocol()


@pytest.fixture
def mock_users_protocol():
    """Provides a mock UsersProtocol instance."""
    return MockUsersProtocol()


@pytest.fixture
def test_app_context(
    mock_queues_protocol,
    mock_issues_protocol,
    mock_global_data_protocol,
    mock_users_protocol,
):
    """Provides a test AppContext with mocked protocol dependencies."""
    return AppContext(
        queues=mock_queues_protocol,
        issues=mock_issues_protocol,
        fields=mock_global_data_protocol,
        users=mock_users_protocol,
    )


@pytest.fixture
def test_settings():
    """Provides test Settings configuration."""
    return Settings(
        tracker_token="test-token",
        tracker_org_id="test-org",
        tools_cache_enabled=False,
        tracker_limit_queues=None,  # No restrictions for most tests
    )


@pytest.fixture
def test_settings_with_queue_limits():
    """Provides test Settings with queue access restrictions."""
    return Settings(
        tracker_token="test-token",
        tracker_org_id="test-org",
        tools_cache_enabled=False,
        tracker_limit_queues="ALLOWED,TEST",  # Comma-separated string
    )


@pytest.fixture
def test_yandex_auth():
    """Provides a test YandexAuth instance."""
    return YandexAuth(token="test-token", org_id="test-org")


# Sample data fixtures
@pytest.fixture
def sample_queue():
    """Provides a sample Queue object."""
    return Queue(
        self="https://api.tracker.yandex.net/v3/queues/TEST",
        id="1",
        version=1,
        key="TEST",
        name="Test Queue",
        lead=User(uid=123, login="test_user", display="Test User"),
        assignAuto=False,
        allowExternals=False,
    )


@pytest.fixture
def sample_issue():
    """Provides a sample Issue object."""
    return Issue(
        self="https://api.tracker.yandex.net/v3/issues/TEST-1",
        id="TEST-1",
        version=1,
        key="TEST-1",
        summary="Test Issue",
        description="Test issue description",
    )


@pytest.fixture
def sample_user():
    """Provides a sample User object."""
    return User(
        uid=123,
        login="test_user",
        display="Test User",
        email="test@example.com",
    )
