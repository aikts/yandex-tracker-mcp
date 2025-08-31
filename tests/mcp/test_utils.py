from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from pytest_mock import MockerFixture

from mcp_tracker.mcp.utils import get_yandex_auth, set_non_needed_fields_null
from mcp_tracker.tracker.proto.common import YandexAuth


class _SampleModel(BaseModel):
    """Test model for set_non_needed_fields_null tests."""

    name: str | None = None
    value: int | None = None
    description: str | None = None


def _create_mock_context(request: Mock | None = None) -> Mock:
    """Create a mock Context object with the given request."""
    ctx = Mock()
    ctx.request_context.request = request
    return ctx


def _create_mock_request(query_params: dict[str, str]) -> Mock:
    """Create a mock Request with given query parameters."""
    request = Mock()
    request.query_params = Mock()
    request.query_params.get = lambda key: query_params.get(key)
    return request


class TestGetYandexAuthWithoutToken:
    def test_no_token_no_request(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        ctx = _create_mock_context(request=None)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(token=None, cloud_org_id=None, org_id=None)

    def test_no_token_with_empty_request(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request({})
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(token=None, cloud_org_id=None, org_id=None)


class TestGetYandexAuthWithToken:
    def test_with_token_no_request(self, mocker: MockerFixture) -> None:
        access_token = Mock()
        access_token.token = "test-oauth-token"
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=access_token,
        )
        ctx = _create_mock_context(request=None)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(
            token="test-oauth-token", cloud_org_id=None, org_id=None
        )

    def test_with_token_and_request(self, mocker: MockerFixture) -> None:
        access_token = Mock()
        access_token.token = "test-oauth-token"
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=access_token,
        )
        request = _create_mock_request({})
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(
            token="test-oauth-token", cloud_org_id=None, org_id=None
        )


class TestGetYandexAuthQueryParams:
    @pytest.mark.parametrize(
        ("query_params", "expected_cloud_org_id", "expected_org_id"),
        [
            ({"cloudOrgId": "cloud-123"}, "cloud-123", None),
            ({"orgId": "org-456"}, None, "org-456"),
            ({"cloudOrgId": "cloud-123", "orgId": "org-456"}, "cloud-123", "org-456"),
        ],
        ids=["cloud_org_id_only", "org_id_only", "both_org_ids"],
    )
    def test_org_id_params(
        self,
        mocker: MockerFixture,
        query_params: dict[str, str],
        expected_cloud_org_id: str | None,
        expected_org_id: str | None,
    ) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request(query_params)
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result.cloud_org_id == expected_cloud_org_id
        assert result.org_id == expected_org_id

    @pytest.mark.parametrize(
        ("query_params", "expected_cloud_org_id", "expected_org_id"),
        [
            ({"cloudOrgId": "  cloud-123  "}, "cloud-123", None),
            ({"orgId": "  org-456  "}, None, "org-456"),
            (
                {"cloudOrgId": "  cloud-123  ", "orgId": "  org-456  "},
                "cloud-123",
                "org-456",
            ),
        ],
        ids=["cloud_org_id_whitespace", "org_id_whitespace", "both_whitespace"],
    )
    def test_whitespace_is_stripped(
        self,
        mocker: MockerFixture,
        query_params: dict[str, str],
        expected_cloud_org_id: str | None,
        expected_org_id: str | None,
    ) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request(query_params)
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result.cloud_org_id == expected_cloud_org_id
        assert result.org_id == expected_org_id

    @pytest.mark.parametrize(
        ("query_params", "expected_cloud_org_id", "expected_org_id"),
        [
            ({"cloudOrgId": ""}, None, None),
            ({"orgId": ""}, None, None),
            ({"cloudOrgId": "   "}, None, None),
            ({"orgId": "   "}, None, None),
            ({"cloudOrgId": "", "orgId": ""}, None, None),
        ],
        ids=[
            "empty_cloud_org_id",
            "empty_org_id",
            "whitespace_only_cloud_org_id",
            "whitespace_only_org_id",
            "both_empty",
        ],
    )
    def test_empty_values_become_none(
        self,
        mocker: MockerFixture,
        query_params: dict[str, str],
        expected_cloud_org_id: str | None,
        expected_org_id: str | None,
    ) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request(query_params)
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result.cloud_org_id == expected_cloud_org_id
        assert result.org_id == expected_org_id


class TestSetNonNeededFieldsNull:
    def test_empty_iterable(self) -> None:
        data: list[_SampleModel] = []

        set_non_needed_fields_null(data, {"name"})

        assert data == []

    def test_all_fields_needed(self) -> None:
        item = _SampleModel(name="test", value=42, description="desc")

        set_non_needed_fields_null([item], {"name", "value", "description"})

        assert item.name == "test"
        assert item.value == 42
        assert item.description == "desc"

    def test_some_fields_not_needed(self) -> None:
        item = _SampleModel(name="test", value=42, description="desc")

        set_non_needed_fields_null([item], {"name"})

        assert item.name == "test"
        assert item.value is None
        assert item.description is None

    def test_no_fields_needed(self) -> None:
        item = _SampleModel(name="test", value=42, description="desc")

        set_non_needed_fields_null([item], set())

        assert item.name is None
        assert item.value is None
        assert item.description is None

    def test_multiple_items(self) -> None:
        items = [
            _SampleModel(name="first", value=1),
            _SampleModel(name="second", value=2),
        ]

        set_non_needed_fields_null(items, {"name"})

        assert items[0].name == "first"
        assert items[0].value is None
        assert items[1].name == "second"
        assert items[1].value is None

    def test_only_set_fields_are_affected(self) -> None:
        item = _SampleModel(name="test")

        set_non_needed_fields_null([item], set())

        assert item.name is None
        assert item.value is None
        assert item.description is None

    def test_unset_fields_with_defaults_remain_unchanged(self) -> None:
        item = _SampleModel(name="test")

        set_non_needed_fields_null([item], {"name"})

        assert item.name == "test"
        assert item.value is None
        assert item.description is None
