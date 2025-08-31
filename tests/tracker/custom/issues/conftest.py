from typing import Any

import pytest


@pytest.fixture
def sample_issue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
        "id": "593cd211ef7e8a33********",
        "key": "TEST-123",
        "version": 1,
        "summary": "Test issue summary",
        "description": "Test issue description",
        "status": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Open",
        },
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
    }


@pytest.fixture
def sample_comment_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123/comments/1",
        "id": 123,
        "text": "This is a test comment",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Test User",
        },
        "createdAt": "2023-01-01T12:00:00.000+0000",
    }
