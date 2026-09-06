from typing import Any

from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.components import Component
from tests.aioresponses_utils import RequestCapture

URL = "https://api.tracker.yandex.net/v3/components/856"


class TestComponentGet:
    async def test_success(
        self, tracker_client: TrackerClient, sample_component_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload=sample_component_data)

        with aioresponses() as m:
            m.get(URL, callback=capture.callback)

            component = await tracker_client.component_get(856)

            assert isinstance(component, Component)
            assert component.id == 856
            assert component.version == 1
            assert component.name == "Design"
            assert component.description == "Design work"
            assert component.assign_auto is False
            assert component.queue is not None
            assert component.queue.key == "AP"
            assert component.lead is not None
            assert component.lead.id == "i.ivanov"
            assert component.lead.display == "Ivan Ivanov"

        capture.assert_called_once()
        assert capture.last_request.url.path == "/v3/components/856"

    async def test_unset_fields_are_absent(
        self,
        tracker_client: TrackerClient,
        sample_bare_component_data: dict[str, Any],
    ) -> None:
        """`description` and `lead` are left out when unset, in and out."""
        with aioresponses() as m:
            m.get(
                "https://api.tracker.yandex.net/v3/components/857",
                payload=sample_bare_component_data,
            )

            component = await tracker_client.component_get(857)

        assert component.description is None
        assert component.lead is None
        dumped = component.model_dump(by_alias=True)
        assert "description" not in dumped
        assert "lead" not in dumped
        assert dumped["assignAuto"] is False

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_component_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_component_data)

        with aioresponses() as m:
            m.get(URL, callback=capture.callback)

            component = await tracker_client_no_org.component_get(
                856, auth=yandex_auth_cloud
            )

            assert component.id == 856

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
