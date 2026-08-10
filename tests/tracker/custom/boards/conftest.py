from typing import Any

import pytest


@pytest.fixture
def sample_board_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/boards/1",
        "id": 1,
        "version": 1,
        "name": "My board",
        "createdAt": "2026-01-22T09:02:18.647+0000",
        "updatedAt": "2026-01-22T09:02:18.647+0000",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1120000000000000",
            "id": "username",
            "display": "Имя Фамилия",
            "cloudUid": "ajevuhegoggfk0000000",
            "passportUid": 1120000000000000,
        },
        "columns": [
            {
                "self": "https://api.tracker.yandex.net/v3/boards/1/columns/1",
                "id": "1",
                "display": "Открыт",
            },
            {
                "self": "https://api.tracker.yandex.net/v3/boards/1/columns/2",
                "id": "2",
                "display": "В работе",
            },
        ],
        "useRanking": False,
        "estimateBy": {
            "self": "https://api.tracker.yandex.net/v3/fields/storyPoints",
            "id": "storyPoints",
            "display": "Story Points",
        },
        "country": {
            "self": "https://api.tracker.yandex.net/v3/countries/1",
            "id": "1",
            "display": "Россия",
        },
        "calendar": {"id": 6},
    }


@pytest.fixture
def sample_sprint_data() -> dict[str, Any]:
    return {
        "self": "https://api.tracker.yandex.net/v3/sprints/4400",
        "id": 4400,
        "version": 1435288720018,
        "name": "Sprint 1",
        "board": {
            "self": "https://api.tracker.yandex.net/v3/boards/3",
            "id": "3",
            "display": "My board",
        },
        "status": "in_progress",
        "archived": False,
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/3300000000",
            "id": "3300000000",
            "display": "Имя Фамилия",
        },
        "createdAt": "2015-06-23T17:03:24.799+0000",
        "startDate": "2015-06-01",
        "endDate": "2015-06-14",
        "startDateTime": "2015-06-01T07:00:00.000+0000",
        "endDateTime": "2015-06-14T07:00:00.000+0000",
    }
