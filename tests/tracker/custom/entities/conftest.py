from typing import Any

import pytest


@pytest.fixture
def sample_entity_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/entities/project/6a43e17349b4e74442327d7f",
        "id": "6a43e17349b4e74442327d7f",
        "version": 1,
        "shortId": 22,
        "entityType": "project",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "fields": {"summary": "Test Project"},
    }
