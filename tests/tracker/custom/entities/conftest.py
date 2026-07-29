from typing import Any

import pytest


@pytest.fixture
def sample_project_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/entities/project/abc123",
        "id": "abc123",
        "shortId": 1,
        "version": 1,
        "entityType": "project",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Project Author",
        },
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "updatedAt": "2024-02-01T00:00:00.000+0000",
        "fields": {
            "summary": "Test Project",
            "description": "A project used for testing",
            "entityStatus": "in_progress",
        },
    }


@pytest.fixture
def sample_project_search_data(sample_project_data: dict[str, Any]) -> dict[str, Any]:
    return {"hits": 1, "pages": 1, "values": [sample_project_data]}


@pytest.fixture
def sample_portfolio_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/entities/portfolio/def456",
        "id": "def456",
        "shortId": 2,
        "version": 1,
        "entityType": "portfolio",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Portfolio Author",
        },
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "updatedAt": "2024-02-01T00:00:00.000+0000",
        "fields": {
            "summary": "Test Portfolio",
            "description": "A portfolio used for testing",
            "entityStatus": "in_progress",
        },
    }


@pytest.fixture
def sample_portfolio_search_data(
    sample_portfolio_data: dict[str, Any],
) -> dict[str, Any]:
    return {"hits": 1, "pages": 1, "values": [sample_portfolio_data]}


@pytest.fixture
def sample_goal_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/entities/goal/ghi789",
        "id": "ghi789",
        "shortId": 3,
        "version": 1,
        "entityType": "goal",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Goal Author",
        },
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "updatedAt": "2024-02-01T00:00:00.000+0000",
        "fields": {
            "summary": "Test Goal",
            "description": "A goal used for testing",
            "entityStatus": "according_to_plan",
            "start": "2024-01-01T00:00:00.000+0000",
            "end": "2024-12-31T23:59:59.000+0000",
        },
    }


@pytest.fixture
def sample_goal_search_data(sample_goal_data: dict[str, Any]) -> dict[str, Any]:
    return {"hits": 1, "pages": 1, "values": [sample_goal_data]}
