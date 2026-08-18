from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import BoardNotFound, TrackerAPIError
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.boards import Board
from tests.aioresponses_utils import RequestCapture


class TestBoardGet:
    async def test_success(
        self, tracker_client: TrackerClient, sample_board_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1",
                payload=sample_board_data,
            )

            board = await tracker_client.board_get(1)

            assert isinstance(board, Board)
            assert board.id == 1
            assert board.name == "My board"
            assert board.useRanking is False
            assert board.estimateBy is not None
            assert board.estimateBy.id == "storyPoints"
            assert board.calendar is not None
            assert board.calendar.id == 6

    async def test_returns_the_auto_filter(
        self,
        tracker_client: TrackerClient,
        sample_board_with_filter_data: dict[str, Any],
    ) -> None:
        """The auto-filter is what says which issues a board collects."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1",
                payload=sample_board_with_filter_data,
            )

            board = await tracker_client.board_get(1)

            assert board.autoFilterSettings is not None
            add = board.autoFilterSettings.addFilterSettings
            assert add is not None
            assert add.enabled is True
            assert add.liveFilter is not None
            fields = add.liveFilter.fieldValues
            assert fields is not None
            assert [f.id for f in fields] == ["queue", "resolution", "statusType"]

            queue_value = fields[0].value
            assert queue_value is not None
            assert queue_value[0].fixed is not None
            assert not isinstance(queue_value[0].fixed, str)
            assert queue_value[0].fixed.key == "LEVELARM"
            assert queue_value[0].invert is False

            remove = board.autoFilterSettings.removeFilterSettings
            assert remove is not None
            assert remove.maxTimeInToRemoveState == "P2W"
            assert remove.statuses is not None
            assert [s.key for s in remove.statuses] == ["closed"]

    async def test_filter_condition_may_be_a_macro_or_a_bare_string(
        self,
        tracker_client: TrackerClient,
        sample_board_with_filter_data: dict[str, Any],
    ) -> None:
        """A condition is a reference, a macro like `empty()`, or a plain string."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1",
                payload=sample_board_with_filter_data,
            )

            board = await tracker_client.board_get(1)

            assert board.autoFilterSettings is not None
            add = board.autoFilterSettings.addFilterSettings
            assert add is not None and add.liveFilter is not None
            fields = add.liveFilter.fieldValues
            assert fields is not None

            resolution = fields[1].value
            assert resolution is not None
            assert resolution[0].macro == "empty()"
            assert resolution[0].fixed is None

            status_type = fields[2].value
            assert status_type is not None
            assert status_type[0].fixed == "new"

    async def test_drops_the_display_order_duplicate(
        self,
        tracker_client: TrackerClient,
        sample_board_with_filter_data: dict[str, Any],
    ) -> None:
        """`filterFieldsOrder` repeats the same fields for the UI and is not modelled."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1",
                payload=sample_board_with_filter_data,
            )

            board = await tracker_client.board_get(1)

            assert board.autoFilterSettings is not None
            add = board.autoFilterSettings.addFilterSettings
            assert add is not None and add.liveFilter is not None
            assert not hasattr(add.liveFilter, "filterFieldsOrder")

    async def test_missing_board_raises_board_not_found(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/99999999",
                status=404,
                payload={"errorMessages": ["Доска не существует."], "statusCode": 404},
            )

            with pytest.raises(BoardNotFound) as exc_info:
                await tracker_client.board_get(99999999)

            assert exc_info.value.board_id == 99999999

    async def test_error_surfaces_the_api_explanation(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1",
                status=403,
                payload={"errorMessages": ["Нет доступа."], "statusCode": 403},
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.board_get(1)

            assert exc_info.value.status == 403
            assert "Нет доступа." in str(exc_info.value)

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_board_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_board_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/boards/1",
                callback=capture.callback,
            )

            board = await tracker_client_no_org.board_get(1, auth=yandex_auth_cloud)

            assert board.id == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
