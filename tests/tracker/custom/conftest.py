from typing import Any

import pytest


@pytest.fixture
def sample_component_data() -> dict[str, Any]:
    """`GET /v3/components/{id}` as the live API answers it (2026-09-06)."""
    return {
        "self": "https://api.tracker.yandex.net/v3/components/856",
        "id": 856,
        "version": 1,
        "name": "Design",
        "description": "Design work",
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/AP",
            "id": "12",
            "key": "AP",
            "display": "Analytics platform",
        },
        "lead": {
            "self": "https://api.tracker.yandex.net/v3/users/1120000000000001",
            "id": "i.ivanov",
            "display": "Ivan Ivanov",
            "cloudUid": "ajevuhegoggfk0000001",
            "passportUid": 1120000000000001,
        },
        "assignAuto": False,
    }


@pytest.fixture
def sample_bare_component_data() -> dict[str, Any]:
    """A component with nothing optional set: `description` and `lead` are absent."""
    return {
        "self": "https://api.tracker.yandex.net/v3/components/857",
        "id": 857,
        "version": 1,
        "name": "Backend",
        "queue": {
            "self": "https://api.tracker.yandex.net/v3/queues/AP",
            "id": "12",
            "key": "AP",
            "display": "Analytics platform",
        },
        "assignAuto": False,
    }
