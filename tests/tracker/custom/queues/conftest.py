from typing import Any

import pytest


@pytest.fixture
def sample_queue_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/queues/TEST",
        "id": 123,
        "key": "TEST",
        "version": 1,
        "name": "Test Queue",
        "description": "A test queue for testing purposes",
        "lead": {
            "self": "https://api.tracker.yandex.net/v3/users/1234567890",
            "id": "user123",
            "display": "Queue Lead",
        },
        "assignAuto": False,
        "defaultType": {
            "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
            "id": "1",
            "key": "task",
            "display": "Task",
        },
        "defaultPriority": {
            "self": "https://api.tracker.yandex.net/v3/priorities/2",
            "id": "2",
            "key": "normal",
            "display": "Normal",
        },
    }


@pytest.fixture
def sample_local_field_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/queues/TEST/localFields/customField1",
        "id": "local-field-123",
        "key": "customField1",
        "version": 1,
        "name": "Custom Field",
        "description": "A custom field for testing",
        "readonly": False,
        "options": True,
        "suggest": False,
        "queryProvider": {"type": "StringOptionalQueryProvider"},
        "order": 1,
        "category": {
            "self": "https://api.tracker.yandex.net/v3/fields/categories/000000000000000000000001",
            "id": "000000000000000000000001",
            "display": "System",
        },
        "type": "ru.yandex.startrek.core.fields.StringFieldType",
    }


@pytest.fixture
def sample_version_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/queues/TEST/versions/1",
        "id": 123,
        "version": 1,
        "name": "1.0.0",
        "description": "Initial release",
        "startDate": "2023-01-01",
        "dueDate": "2023-12-31",
        "released": False,
        "archived": False,
    }


@pytest.fixture
def sample_global_field_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/fields/summary",
        "id": "summary",
        "version": 1,
        "name": "Summary",
        "description": "Issue summary",
        "key": "summary",
        "readonly": False,
        "options": False,
        "suggest": True,
        "queryProvider": {"type": "StringOptionalQueryProvider"},
        "order": 1,
        "category": {
            "self": "https://api.tracker.yandex.net/v3/fields/categories/000000000000000000000001",
            "id": "000000000000000000000001",
            "display": "System",
        },
        "type": "ru.yandex.startrek.core.fields.StringFieldType",
    }
