from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from tests.aioresponses_utils import RequestCapture


class TestIssueTypes:
    @pytest.fixture
    def sample_issue_type_data(self) -> dict[str, Any]:
        return {
            "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
            "id": "1",
            "version": 1,
            "key": "task",
            "name": "Task",
            "description": "General task",
        }

    async def test_get_issue_types_success(
        self, tracker_client: TrackerClient, sample_issue_type_data: dict[str, Any]
    ) -> None:
        types_response = [sample_issue_type_data]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issuetypes", payload=types_response
            )

            result = await tracker_client.get_issue_types()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], IssueType)
            assert result[0].key == "task"
            assert result[0].name == "Task"

    async def test_get_issue_types_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_issue_type_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        types_response = [sample_issue_type_data]
        capture = RequestCapture(payload=types_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issuetypes",
                callback=capture.callback,
            )

            result = await tracker_client_no_org.get_issue_types(auth=yandex_auth_cloud)

            assert isinstance(result, list)
            assert len(result) == 1

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )

    async def test_get_issue_types_empty(self, tracker_client: TrackerClient) -> None:
        types_response: list[dict[str, Any]] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issuetypes", payload=types_response
            )

            result = await tracker_client.get_issue_types()

            assert isinstance(result, list)
            assert len(result) == 0
