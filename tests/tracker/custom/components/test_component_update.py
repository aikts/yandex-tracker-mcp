from typing import Any

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    ComponentEmptyUpdate,
    ComponentVersionConflict,
    FieldClearConflict,
    TrackerAPIError,
)
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.components import Component
from tests.aioresponses_utils import RequestCapture

URL = "https://api.tracker.yandex.net/v3/components/856"


class TestComponentUpdate:
    async def test_success(
        self, tracker_client: TrackerClient, sample_component_data: dict[str, Any]
    ) -> None:
        capture = RequestCapture(payload={**sample_component_data, "version": 2})

        with aioresponses() as m:
            m.patch(f"{URL}?version=1", callback=capture.callback)

            component = await tracker_client.component_update(
                856,
                version=1,
                name="Design",
                description="Design work",
                lead="i.ivanov",
                assign_auto=True,
            )

            assert isinstance(component, Component)
            assert component.id == 856
            assert component.version == 2

        capture.assert_called_once()
        assert capture.last_request.url.path == "/v3/components/856"
        # The version goes as a query parameter: without it the API answers 428.
        capture.last_request.assert_param("version", 1)
        capture.last_request.assert_json_body(
            {
                "name": "Design",
                "description": "Design work",
                "lead": "i.ivanov",
                "assignAuto": True,
            }
        )

    @pytest.mark.parametrize(
        ("kwargs", "expected_body"),
        [
            ({"name": "Backend"}, {"name": "Backend"}),
            ({"description": "Design work"}, {"description": "Design work"}),
            ({"lead": "i.ivanov"}, {"lead": "i.ivanov"}),
            ({"assign_auto": False}, {"assignAuto": False}),
        ],
    )
    async def test_only_the_given_field_is_sent(
        self,
        tracker_client: TrackerClient,
        sample_component_data: dict[str, Any],
        kwargs: dict[str, Any],
        expected_body: dict[str, Any],
    ) -> None:
        capture = RequestCapture(payload=sample_component_data)

        with aioresponses() as m:
            m.patch(f"{URL}?version=1", callback=capture.callback)

            await tracker_client.component_update(856, version=1, **kwargs)

        capture.last_request.assert_json_body(expected_body)

    @pytest.mark.parametrize(
        ("kwargs", "expected_body"),
        [
            ({"clear_lead": True}, {"lead": {}}),
            ({"clear_lead": True, "name": "Design"}, {"name": "Design", "lead": {}}),
        ],
        ids=["alone", "with-name"],
    )
    async def test_clear_lead_sends_an_empty_object(
        self,
        tracker_client: TrackerClient,
        sample_component_data: dict[str, Any],
        kwargs: dict[str, Any],
        expected_body: dict[str, Any],
    ) -> None:
        """Verified live: `{}` removes the lead, while `null` is a silent no-op
        and `""` answers 422. `clear_lead` alone is a valid, non-empty update."""
        payload = {**sample_component_data, "version": 2}
        del payload["lead"]
        capture = RequestCapture(payload=payload)

        with aioresponses() as m:
            m.patch(f"{URL}?version=1", callback=capture.callback)

            component = await tracker_client.component_update(856, version=1, **kwargs)

        capture.assert_called_once()
        capture.last_request.assert_param("version", 1)
        capture.last_request.assert_json_body(expected_body)
        assert component.lead is None
        assert component.version == 2

    async def test_setting_and_clearing_the_lead_raises(
        self, tracker_client: TrackerClient
    ) -> None:
        # No mock registered: no request at all may leave the client.
        with aioresponses() as m:
            with pytest.raises(FieldClearConflict) as exc_info:
                await tracker_client.component_update(
                    856, version=1, lead="i.ivanov", clear_lead=True
                )

            assert not m.requests

        assert "`lead` and `clear_lead`" in str(exc_info.value)

    async def test_empty_update_is_refused_before_any_request(
        self, tracker_client: TrackerClient
    ) -> None:
        """The API answers an empty PATCH with 200 and changes nothing."""
        with aioresponses() as m:
            with pytest.raises(ComponentEmptyUpdate) as exc_info:
                await tracker_client.component_update(856, version=1)

            assert not m.requests

        assert "`clear_lead`" in str(exc_info.value)

    async def test_stale_version_raises_component_version_conflict(
        self, tracker_client: TrackerClient
    ) -> None:
        """A stale component version answers 412, not the 409 issues use."""
        with aioresponses() as m:
            m.patch(
                f"{URL}?version=1",
                status=412,
                payload={
                    "errorMessages": [
                        "Компонент: не удалось сохранить изменения, попробуйте ещё раз."
                    ]
                },
            )

            with pytest.raises(ComponentVersionConflict) as exc_info:
                await tracker_client.component_update(856, version=1, name="Design")

        assert exc_info.value.component_id == 856
        assert exc_info.value.version == 1
        assert "component_get" in str(exc_info.value)

    async def test_error_surfaces_the_api_explanation(
        self, tracker_client: TrackerClient
    ) -> None:
        with aioresponses() as m:
            m.patch(
                f"{URL}?version=1",
                status=422,
                payload={"errors": {"lead": "Пользователь не найден."}},
            )

            with pytest.raises(TrackerAPIError) as exc_info:
                await tracker_client.component_update(856, version=1, lead="nobody")

        assert exc_info.value.status == 422
        assert "lead: Пользователь не найден." in str(exc_info.value)

    async def test_with_auth(
        self,
        tracker_client_no_org: TrackerClient,
        sample_component_data: dict[str, Any],
        yandex_auth_cloud: YandexAuth,
    ) -> None:
        capture = RequestCapture(payload=sample_component_data)

        with aioresponses() as m:
            m.patch(f"{URL}?version=1", callback=capture.callback)

            component = await tracker_client_no_org.component_update(
                856, version=1, name="Design", auth=yandex_auth_cloud
            )

            assert component.id == 856

        capture.assert_called_once()
        capture.last_request.assert_headers(
            {
                "Authorization": "OAuth auth-token",
                "X-Cloud-Org-ID": "cloud-org",
            }
        )
