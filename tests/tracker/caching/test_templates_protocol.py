from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.templates import CommentTemplate, IssueTemplate


class TestCachingTemplatesProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.get_issue_templates.return_value = [
            IssueTemplate(id="1", version=1, name="Bug report")
        ]
        original.get_issue_template.return_value = IssueTemplate(
            id="1", version=1, name="Bug report"
        )
        original.get_comment_templates.return_value = [
            CommentTemplate(id="1", version=1, name="Incident acknowledged")
        ]
        original.get_comment_template.return_value = CommentTemplate(
            id="1", version=1, name="Incident acknowledged"
        )
        return original

    @pytest.fixture
    def caching_templates_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.templates(mock_original)

    async def test_get_issue_templates_calls_original(
        self,
        caching_templates_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_templates_protocol.get_issue_templates(auth=yandex_auth)

        mock_original.get_issue_templates.assert_called_once_with(
            queue=None, per_page=50, page=1, auth=yandex_auth
        )
        assert result == mock_original.get_issue_templates.return_value

    async def test_get_issue_templates_passes_queue_and_pagination(
        self,
        caching_templates_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_templates_protocol.get_issue_templates(
            queue="TEST", per_page=25, page=3, auth=yandex_auth
        )

        mock_original.get_issue_templates.assert_called_once_with(
            queue="TEST", per_page=25, page=3, auth=yandex_auth
        )
        assert result == mock_original.get_issue_templates.return_value

    async def test_get_issue_templates_calls_original_without_auth(
        self, caching_templates_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_templates_protocol.get_issue_templates()

        mock_original.get_issue_templates.assert_called_once_with(
            queue=None, per_page=50, page=1, auth=None
        )
        assert result == mock_original.get_issue_templates.return_value

    async def test_get_issue_template_calls_original(
        self,
        caching_templates_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_templates_protocol.get_issue_template(
            "1", auth=yandex_auth
        )

        mock_original.get_issue_template.assert_called_once_with("1", auth=yandex_auth)
        assert result == mock_original.get_issue_template.return_value

    async def test_get_comment_templates_calls_original(
        self,
        caching_templates_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_templates_protocol.get_comment_templates(
            auth=yandex_auth
        )

        mock_original.get_comment_templates.assert_called_once_with(
            queue=None, per_page=50, page=1, auth=yandex_auth
        )
        assert result == mock_original.get_comment_templates.return_value

    async def test_get_comment_templates_passes_queue_and_pagination(
        self,
        caching_templates_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_templates_protocol.get_comment_templates(
            queue="TEST", per_page=25, page=3, auth=yandex_auth
        )

        mock_original.get_comment_templates.assert_called_once_with(
            queue="TEST", per_page=25, page=3, auth=yandex_auth
        )
        assert result == mock_original.get_comment_templates.return_value

    async def test_get_comment_templates_calls_original_without_auth(
        self, caching_templates_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_templates_protocol.get_comment_templates()

        mock_original.get_comment_templates.assert_called_once_with(
            queue=None, per_page=50, page=1, auth=None
        )
        assert result == mock_original.get_comment_templates.return_value

    async def test_get_comment_template_calls_original(
        self,
        caching_templates_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_templates_protocol.get_comment_template(
            "1", auth=yandex_auth
        )

        mock_original.get_comment_template.assert_called_once_with(
            "1", auth=yandex_auth
        )
        assert result == mock_original.get_comment_template.return_value
