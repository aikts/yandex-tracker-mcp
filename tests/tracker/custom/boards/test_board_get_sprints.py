import datetime
from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import BoardNotFound, TrackerAPIError
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import Sprint
from tests.aioresponses_utils import RequestCapture


class TestBoardGetSprints:
    async def test_success(
        self, tracker_client: TrackerClient, sample_sprint_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/3/sprints",
                payload=[sample_sprint_data],
            )

            result = await tracker_client.board_get_sprints(3)

            assert isinstance(result, list)
            assert len(result) == 1
            sprint = result[0]
            assert isinstance(sprint, Sprint)
            assert sprint.id == 4400
            assert sprint.name == "Sprint 1"
            assert sprint.status == "in_progress"
            assert sprint.archived is False
            assert sprint.board is not None
            assert sprint.board.id == "3"
            assert sprint.board.display == "My board"
            assert sprint.startDate == datetime.date(2015, 6, 1)
            assert sprint.endDate == datetime.date(2015, 6, 14)
            assert sprint.startDateTime == datetime.datetime(
                2015, 6, 1, 7, 0, tzinfo=datetime.timezone.utc
            )
            assert sprint.endDateTime == datetime.datetime(
                2015, 6, 14, 7, 0, tzinfo=datetime.timezone.utc
            )
            assert sprint.createdBy is not None
            assert sprint.createdBy.id == "3300000000"

    @pytest.mark.parametrize(
        "status", ["draft", "in_progress", "released", "archived", "some_new_status"]
    )
    async def test_statuses_are_passed_through(
        self,
        tracker_client: TrackerClient,
        sample_sprint_data: dict[str, Any],
        status: str,
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/3/sprints",
                payload=[{**sample_sprint_data, "status": status}],
            )

            result = await tracker_client.board_get_sprints(3)

            assert result[0].status == status

    async def test_partial_sprint(self, tracker_client: TrackerClient) -> None:
        """A sprint that has not been started yet omits the actual start/end times."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/7/sprints",
                payload=[
                    {
                        "self": "https://api.tracker.yandex.net/v3/sprints/10",
                        "id": 10,
                        "name": "Sprint 2",
                        "status": "draft",
                        "archived": False,
                    }
                ],
            )

            result = await tracker_client.board_get_sprints(7)

            assert len(result) == 1
            sprint = result[0]
            assert sprint.id == 10
            assert sprint.status == "draft"
            assert sprint.startDate is None
            assert sprint.endDate is None
            assert sprint.startDateTime is None
            assert sprint.endDateTime is None

    async def test_empty(self, tracker_client: TrackerClient) -> None:
        sprints_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/42/sprints",
                payload=sprints_response,
            )

            result = await tracker_client.board_get_sprints(42)

            assert result == []

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_sprint_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=[sample_sprint_data])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/3/sprints",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.board_get_sprints(
                3, auth=yandex_auth_cloud
            )

            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_missing_board_raises_board_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/99999999/sprints",
                status=404,
                payload={"errorMessages": ["Доска не существует."], "statusCode": 404},
            )

            with pytest.raises(BoardNotFound) as exc_info:
                await tracker_client.board_get_sprints(99999999)

            assert exc_info.value.board_id == 99999999

    async def test_non_scrum_board_surfaces_the_api_explanation(
        self, tracker_client: TrackerClient
    ) -> None:
        """A board without sprints answers 400, and the reason must reach the caller."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/8/sprints",
                status=400,
                payload={
                    "errors": {},
                    "errorMessages": ["У доски этого типа не может быть спринтов."],
                    "statusCode": 400,
                },
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.board_get_sprints(8)

            assert exc_info.value.status == 400
            assert "У доски этого типа не может быть спринтов." in str(exc_info.value)
