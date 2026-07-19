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


@pytest.fixture
def sample_entity_full() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/entities/project/655f328da834c7631234abcd",
        "id": "655f328da834c7631234abcd",
        "version": 3,
        "shortId": 2,
        "entityType": "project",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
            "cloudUid": "ajevuhegoggf1234",
            "passportUid": 1234567890,
        },
        "createdAt": "2023-11-23T11:07:57.298+0000",
        "updatedAt": "2023-11-23T15:46:26.391+0000",
        "fields": {"summary": "Test Project", "entityStatus": "in_progress"},
    }


@pytest.fixture
def sample_entities_search(sample_entity_full: dict[str, Any]) -> dict[str, Any]:
    return {
        "hits": 2,
        "pages": 1,
        "values": [
            sample_entity_full,
            {
                "self": "https://api.tracker.yandex.net/v3/entities/project/655f8ce5d6a398335678ef01",
                "id": "655f8ce5d6a398335678ef01",
                "version": 7,
                "shortId": 8,
                "entityType": "project",
                "fields": {"entityStatus": "at_risk"},
            },
        ],
    }
