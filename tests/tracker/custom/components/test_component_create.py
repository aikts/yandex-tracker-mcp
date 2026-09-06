from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.components import Component
from tests.aioresponses_utils import RequestCapture

URL = "https://api.tracker.yandex.net/v3/components"


class TestComponentCreate:
    async def test_success_required_fields(
        self, tracker_client: TrackerClient, sample_component_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(status=201, payload=sample_component_data)

        with aioresponses() as m:
            m.post(URL, callback=capture.callback)

            component = await tracker_client.component_create("AP", name="Design")

            assert isinstance(component, Component)
            assert component.id == 856
            assert component.version == 1
            assert component.name == "Design"

        capture.assert_called_once()
        capture.last_request.assert_json_body({"queue": "AP", "name": "Design"})

    async def test_success_optional_fields(
        self, tracker_client: TrackerClient, sample_component_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(status=201, payload=sample_component_data)

        with aioresponses() as m:
            m.post(URL, callback=capture.callback)

            component = await tracker_client.component_create(
                "AP",
                name="Design",
                description="Design work",
                lead="i.ivanov",
                assign_auto=True,
            )

            assert component.lead is not None
            assert component.lead.id == "i.ivanov"

        capture.assert_called_once()
        # `assignAuto` is the wire spelling, `lead` a bare login.
        capture.last_request.assert_json_body(
            {
                "queue": "AP",
                "name": "Design",
                "description": "Design work",
                "lead": "i.ivanov",
                "assignAuto": True,
            }
        )

    @pytest.mark.parametrize(
        ("kwargs", "expected_extra"),
        [
            ({"description": "Design work"}, {"description": "Design work"}),
            ({"lead": "i.ivanov"}, {"lead": "i.ivanov"}),
            ({"assign_auto": False}, {"assignAuto": False}),
        ],
    )
    async def test_only_the_given_optional_field_is_sent(
        self,
        tracker_client: TrackerClient,
        sample_component_data: dict[str, Any],
        kwargs: dict[str, Any],
        expected_extra: dict[str, Any],
    ) -> None:
        capture = RequestCapture(status=201, payload=sample_component_data)

        with aioresponses() as m:
            m.post(URL, callback=capture.callback)

            await tracker_client.component_create("AP", name="Design", **kwargs)

        capture.last_request.assert_json_body(
            {"queue": "AP", "name": "Design", **expected_extra}
        )

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_component_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(status=201, payload=sample_component_data)

        with aioresponses() as m:
            m.post(URL, callback=capture.callback)

            component = await tracker_client_no_org.component_create(
                "AP", name="Design", auth=yandex_auth_cloud
            )

            assert component.id == 856

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
