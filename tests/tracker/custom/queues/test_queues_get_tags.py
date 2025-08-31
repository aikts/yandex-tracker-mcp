from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from tests.aioresponses_utils import RequestCapture


class TestQueuesGetTags:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        tags_response: list[str] = ["bug", "feature", "improvement", "task"]

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/TEST/tags",
                payload=tags_response,
            )

            result = await tracker_client.queues_get_tags("TEST")

            assert isinstance(result, list)
            assert len(result) == 4
            assert all(isinstance(tag, str) for tag in result)
            assert "bug" in result
            assert "feature" in result
            assert "improvement" in result
            assert "task" in result

    async def test_empty(self, tracker_client: TrackerClient) -> None:
        tags_response: list[str] = []

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/EMPTY/tags",
                payload=tags_response,
            )

            result = await tracker_client.queues_get_tags("EMPTY")

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_with_auth(
        self, tracker_client: TrackerClient, yandex_auth: YandexAuth
    ) -> None:
        tags_response = ["urgent", "documentation"]
        capture = RequestCapture(payload=tags_response)

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/queues/DOC/tags",
                callback=capture.callback,
            )

            result = await tracker_client.queues_get_tags("DOC", auth=yandex_auth)

            assert isinstance(result, list)
            assert len(result) == 2
            assert "urgent" in result
            assert "documentation" in result

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Org-ID": "auth-org",
            }
        )
