from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.workflows import Workflow
from tests.aioresponses_utils import RequestCapture


class TestGetWorkflows:
    async def test_success(self, tracker_client: TrackerClient) -> None:
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/workflows",
                payload=[{"id": "W1", "name": "Default"}, {"id": "W2"}],
            )

            result = await tracker_client.get_workflows()

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(w, Workflow) for w in result)
            assert result[0].id == "W1"
            assert result[0].name == "Default"

    async def test_with_auth(
        self, tracker_client_no_org: TrackerClient, yandex_auth_cloud: YandexAuth
    ) -> None:
        capture = RequestCapture(payload=[{"id": "W1"}])

        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/workflows",
                callback=capture.callback,
            )

            await tracker_client_no_org.get_workflows(auth=yandex_auth_cloud)

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {"Authorization": "OAuth auth-token", "X-Cloud-Org-ID": "cloud-org"}
        )
