from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueTransition,
    Worklog,
)
from mcp_tracker.tracker.proto.types.refs import IssueReference


class TestCachingIssuesProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.issue_get.return_value = Issue(key="TEST-1", summary="Test Issue")
        original.issues_get_links.return_value = [
            IssueLink(
                id=1,
                object=IssueReference(
                    id="TEST-2", key="TEST-2", display="Linked Issue"
                ),
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
        original.issue_get_transitions.return_value = [
            IssueTransition(id="close", display="Close")
        ]
        original.issue_create.return_value = Issue(key="TEST-2", summary="New Issue")
        original.issue_execute_transition.return_value = [
            IssueTransition(id="reopen", display="Reopen")
        ]
        original.issue_close.return_value = [
            IssueTransition(id="reopen", display="Reopen")
        ]
        original.issue_update.return_value = Issue(
            key="TEST-1", summary="Updated Issue"
        )
        original.worklogs_search.return_value = [Worklog(id=1, comment="Search result")]
        return original

    @pytest.fixture
    def caching_issues_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.issues(mock_original)

    async def test_issue_get_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issue_get("TEST-1", auth=yandex_auth)

        mock_original.issue_get.assert_called_once_with("TEST-1", auth=yandex_auth)
        assert result == mock_original.issue_get.return_value

    async def test_issues_get_links_calls_original(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issues_get_links("TEST-1")

        mock_original.issues_get_links.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issues_get_links.return_value

    async def test_issue_get_comments_calls_original(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_get_comments("TEST-1")

        mock_original.issue_get_comments.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_comments.return_value

    async def test_issues_find_calls_original_with_all_params(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issues_find(
            "query", per_page=20, page=3, auth=yandex_auth
        )

        mock_original.issues_find.assert_called_once_with(
            query="query", per_page=20, page=3, auth=yandex_auth
        )
        assert result == mock_original.issues_find.return_value

    async def test_issue_get_worklogs_calls_original(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_get_worklogs("TEST-1")

        mock_original.issue_get_worklogs.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_worklogs.return_value

    async def test_issue_get_attachments_calls_original(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_get_attachments("TEST-1")

        mock_original.issue_get_attachments.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_attachments.return_value

    async def test_issues_count_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issues_count(
            "test query", auth=yandex_auth
        )

        mock_original.issues_count.assert_called_once_with(
            "test query", auth=yandex_auth
        )
        assert result == mock_original.issues_count.return_value

    async def test_issue_get_checklist_calls_original(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_get_checklist("TEST-1")

        mock_original.issue_get_checklist.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_checklist.return_value

    async def test_issue_get_transitions_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issue_get_transitions(
            "TEST-1", auth=yandex_auth
        )

        mock_original.issue_get_transitions.assert_called_once_with(
            "TEST-1", auth=yandex_auth
        )
        assert result == mock_original.issue_get_transitions.return_value

    async def test_issue_get_transitions_calls_original_without_auth(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_get_transitions("TEST-1")

        mock_original.issue_get_transitions.assert_called_once_with("TEST-1", auth=None)
        assert result == mock_original.issue_get_transitions.return_value

    async def test_issue_create_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issue_create(
            "TEST",
            "New Issue",
            type=1,
            description="Test description",
            assignee="user1",
            priority="high",
            parent="TEST-1",
            sprint=["sprint-1"],
            auth=yandex_auth,
        )

        mock_original.issue_create.assert_called_once_with(
            "TEST",
            "New Issue",
            type=1,
            description="Test description",
            assignee="user1",
            priority="high",
            parent="TEST-1",
            sprint=["sprint-1"],
            auth=yandex_auth,
        )
        assert result == mock_original.issue_create.return_value

    async def test_issue_create_calls_original_with_minimal_params(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_create("TEST", "New Issue")

        mock_original.issue_create.assert_called_once_with(
            "TEST",
            "New Issue",
            type=None,
            description=None,
            assignee=None,
            priority=None,
            parent=None,
            sprint=None,
            auth=None,
        )
        assert result == mock_original.issue_create.return_value

    async def test_issue_execute_transition_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issue_execute_transition(
            "TEST-1",
            "close",
            comment="Closing issue",
            fields={"resolution": "fixed"},
            auth=yandex_auth,
        )

        mock_original.issue_execute_transition.assert_called_once_with(
            "TEST-1",
            "close",
            comment="Closing issue",
            fields={"resolution": "fixed"},
            auth=yandex_auth,
        )
        assert result == mock_original.issue_execute_transition.return_value

    async def test_issue_execute_transition_calls_original_with_minimal_params(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_execute_transition(
            "TEST-1", "close"
        )

        mock_original.issue_execute_transition.assert_called_once_with(
            "TEST-1",
            "close",
            comment=None,
            fields=None,
            auth=None,
        )
        assert result == mock_original.issue_execute_transition.return_value

    async def test_issue_close_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issue_close(
            "TEST-1",
            "fixed",
            comment="Done",
            fields={"version": "1.0"},
            auth=yandex_auth,
        )

        mock_original.issue_close.assert_called_once_with(
            "TEST-1",
            "fixed",
            comment="Done",
            fields={"version": "1.0"},
            auth=yandex_auth,
        )
        assert result == mock_original.issue_close.return_value

    async def test_issue_close_calls_original_with_minimal_params(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_close("TEST-1", "fixed")

        mock_original.issue_close.assert_called_once_with(
            "TEST-1",
            "fixed",
            comment=None,
            fields=None,
            auth=None,
        )
        assert result == mock_original.issue_close.return_value

    async def test_issue_update_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.issue_update(
            "TEST-1",
            summary="Updated Summary",
            description="Updated description",
            tags=["tag1", "tag2"],
            auth=yandex_auth,
        )

        mock_original.issue_update.assert_called_once_with(
            "TEST-1",
            summary="Updated Summary",
            description="Updated description",
            markup_type=None,
            parent=None,
            sprint=None,
            type=None,
            priority=None,
            followers=None,
            project=None,
            attachment_ids=None,
            description_attachment_ids=None,
            tags=["tag1", "tag2"],
            version=None,
            auth=yandex_auth,
        )
        assert result == mock_original.issue_update.return_value

    async def test_issue_update_calls_original_with_minimal_params(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.issue_update("TEST-1")

        mock_original.issue_update.assert_called_once_with(
            "TEST-1",
            summary=None,
            description=None,
            markup_type=None,
            parent=None,
            sprint=None,
            type=None,
            priority=None,
            followers=None,
            project=None,
            attachment_ids=None,
            description_attachment_ids=None,
            tags=None,
            version=None,
            auth=None,
        )
        assert result == mock_original.issue_update.return_value

    async def test_worklogs_search_calls_original(
        self,
        caching_issues_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_issues_protocol.worklogs_search(
            created_by="john.doe",
            created_at_from="2024-01-01T00:00:00.000+0000",
            created_at_to="2024-12-31T23:59:59.999+0000",
            auth=yandex_auth,
        )

        mock_original.worklogs_search.assert_called_once_with(
            created_by="john.doe",
            created_at_from="2024-01-01T00:00:00.000+0000",
            created_at_to="2024-12-31T23:59:59.999+0000",
            auth=yandex_auth,
        )
        assert result == mock_original.worklogs_search.return_value

    async def test_worklogs_search_calls_original_with_minimal_params(
        self, caching_issues_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_issues_protocol.worklogs_search()

        mock_original.worklogs_search.assert_called_once_with(
            created_by=None,
            created_at_from=None,
            created_at_to=None,
            auth=None,
        )
        assert result == mock_original.worklogs_search.return_value
