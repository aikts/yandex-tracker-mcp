from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import IssueNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import Issue
from tests.aioresponses_utils import RequestCapture


class TestIssueGet:
    async def test_success(
        self, tracker_client: TrackerClient, sample_issue_data: dict[str, Any]
    ) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                payload=sample_issue_data,
            )

            result = await tracker_client.issue_get("TEST-123")

            assert isinstance(result, Issue)
            assert result.key == "TEST-123"
            assert result.summary == "Test issue summary"
            assert result.description == "Test issue description"

    async def test_with_auth(
        self,
        tracker_client: TrackerClient,
        sample_issue_data: dict[str, Any],
        yandex_auth: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_issue_data)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/issues/TEST-123",
                callback=capture.callback,
            )

            result = await tracker_client.issue_get("TEST-123", auth=yandex_auth)

            assert isinstance(result, Issue)
            assert result.key == "TEST-123"

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )

    async def test_not_found(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get("https://api.tracker.yandex.net/v3/issues/NOTFOUND-123", status=404)

            with pytest.raises(IssueNotFound) as exc_info:
                await tracker_client.issue_get("NOTFOUND-123")

            assert exc_info.value.issue_id == "NOTFOUND-123"
