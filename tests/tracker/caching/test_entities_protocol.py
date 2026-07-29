from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import (
    GoalEntity,
    GoalSearchResult,
    PortfolioEntity,
    PortfolioSearchResult,
    ProjectEntity,
    ProjectSearchResult,
)


class TestCachingEntitiesProtocol:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.project_get.return_value = ProjectEntity(id="p1", entityType="project")
        original.project_find.return_value = ProjectSearchResult(
            hits=0, pages=0, values=[]
        )
        original.portfolio_get.return_value = PortfolioEntity(
            id="pf1", entityType="portfolio"
        )
        original.portfolio_find.return_value = PortfolioSearchResult(
            hits=0, pages=0, values=[]
        )
        original.goal_get.return_value = GoalEntity(id="g1", entityType="goal")
        original.goal_find.return_value = GoalSearchResult(hits=0, pages=0, values=[])
        return original

    @pytest.fixture
    def caching_entities_protocol(self, mock_original: AsyncMock) -> Any:
        cache_config = {"ttl": 300}
        cache_collection = make_cached_protocols(cache_config)
        return cache_collection.entities(mock_original)

    async def test_project_get_calls_original_with_auth(
        self,
        caching_entities_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_entities_protocol.project_get(
            "p1", fields=["summary"], auth=yandex_auth
        )

        mock_original.project_get.assert_called_once_with(
            "p1", fields=["summary"], auth=yandex_auth
        )
        assert result == mock_original.project_get.return_value

    async def test_project_get_calls_original_without_auth(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_entities_protocol.project_get("p1")

        mock_original.project_get.assert_called_once_with("p1", fields=None, auth=None)
        assert result == mock_original.project_get.return_value

    async def test_project_find_calls_original(
        self,
        caching_entities_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_entities_protocol.project_find(
            input="test", per_page=10, page=1, auth=yandex_auth
        )

        mock_original.project_find.assert_called_once_with(
            input="test",
            filter=None,
            order_by=None,
            order_asc=None,
            root_only=None,
            per_page=10,
            page=1,
            fields=None,
            auth=yandex_auth,
        )
        assert result == mock_original.project_find.return_value

    async def test_portfolio_get_calls_original(
        self,
        caching_entities_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_entities_protocol.portfolio_get("pf1", auth=yandex_auth)

        mock_original.portfolio_get.assert_called_once_with(
            "pf1", fields=None, auth=yandex_auth
        )
        assert result == mock_original.portfolio_get.return_value

    async def test_portfolio_find_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_entities_protocol.portfolio_find(root_only=True)

        mock_original.portfolio_find.assert_called_once_with(
            input=None,
            filter=None,
            order_by=None,
            order_asc=None,
            root_only=True,
            per_page=50,
            page=1,
            fields=None,
            auth=None,
        )
        assert result == mock_original.portfolio_find.return_value

    async def test_goal_get_calls_original(
        self,
        caching_entities_protocol: Any,
        mock_original: AsyncMock,
        yandex_auth: YandexAuth,
    ) -> None:
        result = await caching_entities_protocol.goal_get("g1", auth=yandex_auth)

        mock_original.goal_get.assert_called_once_with(
            "g1", fields=None, auth=yandex_auth
        )
        assert result == mock_original.goal_get.return_value

    async def test_goal_find_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_entities_protocol.goal_find(
            filter={"entityStatus": "achieved"}
        )

        mock_original.goal_find.assert_called_once_with(
            input=None,
            filter={"entityStatus": "achieved"},
            order_by=None,
            order_asc=None,
            root_only=None,
            per_page=50,
            page=1,
            fields=None,
            auth=None,
        )
        assert result == mock_original.goal_find.return_value

    async def test_project_create_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        mock_original.project_create.return_value = ProjectEntity(
            id="p2", entityType="project"
        )

        result = await caching_entities_protocol.project_create(summary="New Project")

        mock_original.project_create.assert_called_once_with(
            summary="New Project",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            links=None,
            auth=None,
        )
        assert result == mock_original.project_create.return_value

    async def test_project_update_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_entities_protocol.project_update(
            "p1", summary="Renamed", version=2
        )

        mock_original.project_update.assert_called_once_with(
            "p1",
            summary="Renamed",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            links=None,
            comment=None,
            version=2,
            auth=None,
        )
        assert result == mock_original.project_update.return_value

    async def test_project_delete_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        mock_original.project_delete.return_value = None

        result = await caching_entities_protocol.project_delete("p1", with_board=True)

        mock_original.project_delete.assert_called_once_with(
            "p1", with_board=True, auth=None
        )
        assert result is None

    async def test_portfolio_create_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        mock_original.portfolio_create.return_value = PortfolioEntity(
            id="pf2", entityType="portfolio"
        )

        result = await caching_entities_protocol.portfolio_create(
            summary="New Portfolio"
        )

        mock_original.portfolio_create.assert_called_once_with(
            summary="New Portfolio",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            links=None,
            auth=None,
        )
        assert result == mock_original.portfolio_create.return_value

    async def test_portfolio_update_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_entities_protocol.portfolio_update(
            "pf1", entity_status="cancelled"
        )

        mock_original.portfolio_update.assert_called_once_with(
            "pf1",
            summary=None,
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            start=None,
            end=None,
            tags=None,
            entity_status="cancelled",
            parent_entity=None,
            team_access=None,
            links=None,
            comment=None,
            version=None,
            auth=None,
        )
        assert result == mock_original.portfolio_update.return_value

    async def test_portfolio_delete_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        mock_original.portfolio_delete.return_value = None

        result = await caching_entities_protocol.portfolio_delete("pf1")

        mock_original.portfolio_delete.assert_called_once_with(
            "pf1", with_board=False, auth=None
        )
        assert result is None

    async def test_goal_create_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        mock_original.goal_create.return_value = GoalEntity(id="g2", entityType="goal")

        result = await caching_entities_protocol.goal_create(summary="New Goal")

        mock_original.goal_create.assert_called_once_with(
            summary="New Goal",
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            links=None,
            auth=None,
        )
        assert result == mock_original.goal_create.return_value

    async def test_goal_update_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        result = await caching_entities_protocol.goal_update(
            "g1", comment="progress update"
        )

        mock_original.goal_update.assert_called_once_with(
            "g1",
            summary=None,
            description=None,
            lead=None,
            team_users=None,
            clients=None,
            followers=None,
            end=None,
            tags=None,
            entity_status=None,
            parent_entity=None,
            team_access=None,
            links=None,
            comment="progress update",
            version=None,
            auth=None,
        )
        assert result == mock_original.goal_update.return_value

    async def test_goal_delete_calls_original(
        self, caching_entities_protocol: Any, mock_original: AsyncMock
    ) -> None:
        mock_original.goal_delete.return_value = None

        result = await caching_entities_protocol.goal_delete("g1")

        mock_original.goal_delete.assert_called_once_with(
            "g1", with_board=False, auth=None
        )
        assert result is None
