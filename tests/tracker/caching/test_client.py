from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User


class TestMakeCachedProtocols:
    def test_make_cached_protocols_returns_four_classes(self):
        cache_config = {"ttl": 300}

        result = make_cached_protocols(cache_config)

        assert len(result) == 4
        queues_class, issues_class, global_data_class, users_class = result

        # Verify all returned items are classes
        assert isinstance(queues_class, type)
        assert isinstance(issues_class, type)
        assert isinstance(global_data_class, type)
        assert isinstance(users_class, type)

    def test_cached_classes_have_expected_names(self):
        cache_config = {"ttl": 300}

        queues_class, issues_class, global_data_class, users_class = (
            make_cached_protocols(cache_config)
        )

        assert queues_class.__name__ == "CachingQueuesProtocol"
        assert issues_class.__name__ == "CachingIssuesProtocol"
        assert global_data_class.__name__ == "CachingGlobalDataProtocol"
        assert users_class.__name__ == "CachingUsersProtocol"


class TestCachingQueuesProtocol:
    @pytest.fixture
    def mock_original(self):
        original = AsyncMock()
        original.queues_list.return_value = [Queue(id=1, key="TEST", name="Test Queue")]
        original.queues_get_local_fields.return_value = [
            LocalField(id="test-field", key="test", name="Test Field")
        ]
        original.queues_get_tags.return_value = ["tag1", "tag2"]
        original.queues_get_versions.return_value = [
            QueueVersion(id=1, version=1, name="1.0", released=False, archived=False)
        ]
        return original

    @pytest.fixture
    def caching_queues_protocol(self, mock_original):
        cache_config = {"ttl": 300}
        queues_class, _, _, _ = make_cached_protocols(cache_config)
        return queues_class(mock_original)

    async def test_queues_list_calls_original_with_auth(
        self, caching_queues_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_queues_protocol.queues_list(
            per_page=50, page=2, auth=auth
        )

        mock_original.queues_list.assert_called_once_with(
            per_page=50, page=2, auth=auth
        )
        assert result == mock_original.queues_list.return_value

    async def test_queues_list_calls_original_without_auth(
        self, caching_queues_protocol, mock_original
    ):
        result = await caching_queues_protocol.queues_list(per_page=100, page=1)

        mock_original.queues_list.assert_called_once_with(
            per_page=100, page=1, auth=None
        )
        assert result == mock_original.queues_list.return_value

    async def test_queues_get_local_fields_calls_original(
        self, caching_queues_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_queues_protocol.queues_get_local_fields(
            "TEST", auth=auth
        )

        mock_original.queues_get_local_fields.assert_called_once_with("TEST", auth=auth)
        assert result == mock_original.queues_get_local_fields.return_value

    async def test_queues_get_tags_calls_original(
        self, caching_queues_protocol, mock_original
    ):
        result = await caching_queues_protocol.queues_get_tags("TEST")

        mock_original.queues_get_tags.assert_called_once_with("TEST", auth=None)
        assert result == mock_original.queues_get_tags.return_value

    async def test_queues_get_versions_calls_original(
        self, caching_queues_protocol, mock_original
    ):
        result = await caching_queues_protocol.queues_get_versions("TEST")

        mock_original.queues_get_versions.assert_called_once_with("TEST", auth=None)
        assert result == mock_original.queues_get_versions.return_value


class TestCachingIssuesProtocol:
    @pytest.fixture
    def mock_original(self):
        original = AsyncMock()
        original.issue_get.return_value = Issue(key="TEST-1", summary="Test Issue")
        original.issues_get_links.return_value = [
            IssueLink(
                id=1,
                object={"id": "TEST-2", "key": "TEST-2", "display": "Linked Issue"},
            )
        ]
        original.issue_get_comments.return_value = [
            IssueComment(id=1, text="Test comment")
        ]
        original.issues_find.return_value = [Issue(key="TEST-1", summary="Test Issue")]
        original.issue_get_worklogs.return_value = [Worklog(id=1)]
        original.issue_get_attachments.return_value = [
            IssueAttachment(id="att-1", name="test.txt")
        ]
        original.issues_count.return_value = 42
        original.issue_get_checklist.return_value = [
            ChecklistItem(id="item-1", text="Test item")
        ]
        return original

    @pytest.fixture
    def caching_issues_protocol(self, mock_original):
        cache_config = {"ttl": 300}
        _, issues_class, _, _ = make_cached_protocols(cache_config)
        return issues_class(mock_original)

    async def test_issue_get_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_issues_protocol.issue_get("TEST-1", auth=auth)

        mock_original.issue_get.assert_called_once_with("TEST-1", auth=auth)
        assert result == mock_original.issue_get.return_value

    async def test_issues_get_links_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        result = await caching_issues_protocol.issues_get_links("TEST-1")

        mock_original.issues_get_links.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issues_get_links.return_value

    async def test_issue_get_comments_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        result = await caching_issues_protocol.issue_get_comments("TEST-1")

        mock_original.issue_get_comments.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_comments.return_value

    async def test_issues_find_calls_original_with_all_params(
        self, caching_issues_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_issues_protocol.issues_find(
            "query", per_page=20, page=3, auth=auth
        )

        mock_original.issues_find.assert_called_once_with(
            query="query", per_page=20, page=3, auth=auth
        )
        assert result == mock_original.issues_find.return_value

    async def test_issue_get_worklogs_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        result = await caching_issues_protocol.issue_get_worklogs("TEST-1")

        mock_original.issue_get_worklogs.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_worklogs.return_value

    async def test_issue_get_attachments_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        result = await caching_issues_protocol.issue_get_attachments("TEST-1")

        mock_original.issue_get_attachments.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_attachments.return_value

    async def test_issues_count_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_issues_protocol.issues_count("test query", auth=auth)

        mock_original.issues_count.assert_called_once_with("test query", auth=auth)
        assert result == mock_original.issues_count.return_value

    async def test_issue_get_checklist_calls_original(
        self, caching_issues_protocol, mock_original
    ):
        result = await caching_issues_protocol.issue_get_checklist("TEST-1")

        mock_original.issue_get_checklist.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_checklist.return_value


class TestCachingGlobalDataProtocol:
    @pytest.fixture
    def mock_original(self):
        original = AsyncMock()
        original.get_global_fields.return_value = [
            GlobalField(id="status-field", key="status", name="Status")
        ]
        original.get_statuses.return_value = [
            Status(version=1, key="open", name="Open", order=1, type="new")
        ]
        original.get_issue_types.return_value = [
            IssueType(id=1, version=1, key="task", name="Task")
        ]
        original.get_priorities.return_value = [
            Priority(version=1, key="high", name="High", order=1)
        ]
        return original

    @pytest.fixture
    def caching_global_data_protocol(self, mock_original):
        cache_config = {"ttl": 300}
        _, _, global_data_class, _ = make_cached_protocols(cache_config)
        return global_data_class(mock_original)

    async def test_get_global_fields_calls_original(
        self, caching_global_data_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_global_data_protocol.get_global_fields(auth=auth)

        mock_original.get_global_fields.assert_called_once_with(auth=auth)
        assert result == mock_original.get_global_fields.return_value

    async def test_get_statuses_calls_original(
        self, caching_global_data_protocol, mock_original
    ):
        result = await caching_global_data_protocol.get_statuses()

        mock_original.get_statuses.assert_called_once_with(auth=None)
        assert result == mock_original.get_statuses.return_value

    async def test_get_issue_types_calls_original(
        self, caching_global_data_protocol, mock_original
    ):
        result = await caching_global_data_protocol.get_issue_types()

        mock_original.get_issue_types.assert_called_once_with(auth=None)
        assert result == mock_original.get_issue_types.return_value

    async def test_get_priorities_calls_original(
        self, caching_global_data_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_global_data_protocol.get_priorities(auth=auth)

        mock_original.get_priorities.assert_called_once_with(auth=auth)
        assert result == mock_original.get_priorities.return_value


class TestCachingUsersProtocol:
    @pytest.fixture
    def mock_original(self):
        original = AsyncMock()
        original.users_list.return_value = [
            User(uid=123, login="test_user", display="Test User")
        ]
        original.user_get.return_value = User(
            uid=123, login="test_user", display="Test User"
        )
        original.user_get_current.return_value = User(
            uid=456, login="current_user", display="Current User"
        )
        return original

    @pytest.fixture
    def caching_users_protocol(self, mock_original):
        cache_config = {"ttl": 300}
        _, _, _, users_class = make_cached_protocols(cache_config)
        return users_class(mock_original)

    async def test_users_list_calls_original(
        self, caching_users_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_users_protocol.users_list(per_page=25, page=2, auth=auth)

        mock_original.users_list.assert_called_once_with(per_page=25, page=2, auth=auth)
        assert result == mock_original.users_list.return_value

    async def test_user_get_calls_original(self, caching_users_protocol, mock_original):
        result = await caching_users_protocol.user_get("test_user")

        mock_original.user_get.assert_called_once_with("test_user", auth=None)
        assert result == mock_original.user_get.return_value

    async def test_user_get_current_calls_original(
        self, caching_users_protocol, mock_original
    ):
        auth = YandexAuth(token="test-token", org_id="test-org")

        result = await caching_users_protocol.user_get_current(auth=auth)

        mock_original.user_get_current.assert_called_once_with(auth=auth)
        assert result == mock_original.user_get_current.return_value
