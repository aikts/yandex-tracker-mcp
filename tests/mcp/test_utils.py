from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from pytest_mock import MockerFixture

from mcp_tracker.mcp.utils import (
    get_yandex_auth,
    resolve_issue_attachment_local_path,
    save_issue_attachment_file,
    set_non_needed_fields_null,
)
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


def _create_mock_request(
    query_params: dict[str, str], headers: dict[str, str] | None = None
) -> Mock:
    """Create a mock Request with given query parameters and headers."""
    request = Mock()
    request.headers = headers or {}
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


class TestGetYandexAuthWithPassthroughBearer:
    @pytest.mark.parametrize(
        ("auth_header", "expected_token"),
        [
            ("Bearer passthrough-token", "passthrough-token"),
            ("Bearer   passthrough-token  ", "passthrough-token"),
        ],
        ids=["bearer_token", "bearer_token_with_whitespace"],
    )
    def test_uses_bearer_header_when_access_token_missing(
        self,
        mocker: MockerFixture,
        auth_header: str,
        expected_token: str,
    ) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request({}, {"Authorization": auth_header})
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(
            token=expected_token, cloud_org_id=None, org_id=None
        )

    @pytest.mark.parametrize(
        "auth_header",
        [
            "Bearer   ",
            "OAuth passthrough-token",
            "Basic passthrough-token",
            "",
        ],
        ids=["empty_bearer", "oauth_header", "basic_header", "empty_header"],
    )
    def test_ignores_invalid_bearer_header(
        self,
        mocker: MockerFixture,
        auth_header: str,
    ) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request({}, {"Authorization": auth_header})
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(token=None, cloud_org_id=None, org_id=None)

    def test_access_token_has_priority_over_bearer_header(
        self, mocker: MockerFixture
    ) -> None:
        access_token = Mock()
        access_token.token = "test-oauth-token"
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=access_token,
        )
        request = _create_mock_request(
            {}, {"Authorization": "Bearer passthrough-token"}
        )
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(
            token="test-oauth-token", cloud_org_id=None, org_id=None
        )

    def test_bearer_header_with_org_query_params(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "mcp_tracker.mcp.utils.get_access_token",
            return_value=None,
        )
        request = _create_mock_request(
            {"cloudOrgId": "  cloud-123  ", "orgId": "  org-456  "},
            {"Authorization": "Bearer passthrough-token"},
        )
        ctx = _create_mock_context(request=request)

        result = get_yandex_auth(ctx)

        assert result == YandexAuth(
            token="passthrough-token",
            cloud_org_id="cloud-123",
            org_id="org-456",
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


class TestResolveIssueAttachmentLocalPath:
    async def test_resolves_path_inside_sandbox(self, tmp_path: Path) -> None:
        base_dir = tmp_path / "sandbox"
        save_directory = base_dir / "attachments"

        local_path = await resolve_issue_attachment_local_path(
            issue_id="HELPDESK-1054",
            attachment_id="7699",
            file_name="image.png",
            save_directory=str(save_directory),
            attachments_base_dir=base_dir,
        )

        assert local_path == save_directory.resolve() / "HELPDESK-1054-7699.png"
        assert save_directory.resolve().is_dir()
        assert not local_path.exists()

    async def test_rejects_existing_local_path(self, tmp_path: Path) -> None:
        base_dir = tmp_path / "sandbox"
        save_directory = base_dir / "attachments"
        existing = save_directory / "TEST-1-42.png"
        save_directory.mkdir(parents=True)
        existing.write_bytes(b"old")

        with pytest.raises(ValueError, match="Attachment file already exists"):
            await resolve_issue_attachment_local_path(
                issue_id="TEST-1",
                attachment_id="42",
                file_name="image.png",
                save_directory=str(save_directory),
                attachments_base_dir=base_dir,
            )

    async def test_rejects_save_directory_that_is_file(self, tmp_path: Path) -> None:
        base_dir = tmp_path / "sandbox"
        save_directory = base_dir / "not-a-dir"
        base_dir.mkdir(parents=True)
        save_directory.write_bytes(b"blocker")

        with pytest.raises(ValueError, match="save_directory is a file"):
            await resolve_issue_attachment_local_path(
                issue_id="TEST-1",
                attachment_id="1",
                file_name="file.txt",
                save_directory=str(save_directory),
                attachments_base_dir=base_dir,
            )


class TestSaveIssueAttachmentFile:
    async def test_saves_file_with_issue_and_attachment_id(
        self, tmp_path: Path
    ) -> None:
        data = b"file content"
        base_dir = tmp_path / "sandbox"
        save_directory = base_dir / "attachments"

        local_path = await save_issue_attachment_file(
            data,
            issue_id="HELPDESK-1054",
            attachment_id="7699",
            file_name="image.png",
            save_directory=str(save_directory),
            attachments_base_dir=base_dir,
        )

        assert local_path == save_directory.resolve() / "HELPDESK-1054-7699.png"
        assert local_path.read_bytes() == data

    async def test_does_not_overwrite_existing_file(self, tmp_path: Path) -> None:
        base_dir = tmp_path / "sandbox"
        save_directory = base_dir / "attachments"
        original = b"original"
        replacement = b"replacement"

        await save_issue_attachment_file(
            original,
            issue_id="TEST-1",
            attachment_id="1",
            file_name="file.txt",
            save_directory=str(save_directory),
            attachments_base_dir=base_dir,
        )

        with pytest.raises(ValueError, match="Attachment file already exists"):
            await save_issue_attachment_file(
                replacement,
                issue_id="TEST-1",
                attachment_id="1",
                file_name="file.txt",
                save_directory=str(save_directory),
                attachments_base_dir=base_dir,
            )

        local_path = save_directory.resolve() / "TEST-1-1.txt"
        assert local_path.read_bytes() == original

    async def test_uses_basename_only(self, tmp_path: Path) -> None:
        data = b"safe content"
        base_dir = tmp_path / "sandbox"

        local_path = await save_issue_attachment_file(
            data,
            issue_id="TEST-1",
            attachment_id="1",
            file_name="../../etc/passwd",
            save_directory=str(base_dir),
            attachments_base_dir=base_dir,
        )

        assert local_path.name == "TEST-1-1"
        assert local_path.read_bytes() == data

    @pytest.mark.parametrize(
        ("file_name", "expected_suffix"),
        [
            ("report.pdf", ".pdf"),
            ("archive.tar.gz", ".gz"),
            ("noextension", ""),
        ],
    )
    async def test_preserves_file_suffix(
        self,
        tmp_path: Path,
        file_name: str,
        expected_suffix: str,
    ) -> None:
        base_dir = tmp_path / "sandbox"
        local_path = await save_issue_attachment_file(
            b"x",
            issue_id="TEST-1",
            attachment_id="42",
            file_name=file_name,
            save_directory=str(base_dir),
            attachments_base_dir=base_dir,
        )

        assert local_path.suffix == expected_suffix

    @pytest.mark.parametrize(
        ("issue_id", "attachment_id"),
        [
            ("TEST/1", "42"),
            ("TEST-1", "../42"),
            ("TEST 1", "42"),
        ],
    )
    async def test_rejects_unsafe_identifiers(
        self,
        tmp_path: Path,
        issue_id: str,
        attachment_id: str,
    ) -> None:
        base_dir = tmp_path / "sandbox"
        with pytest.raises(ValueError):
            await save_issue_attachment_file(
                b"x",
                issue_id=issue_id,
                attachment_id=attachment_id,
                file_name="report.pdf",
                save_directory=str(base_dir),
                attachments_base_dir=base_dir,
            )

    async def test_allows_path_inside_base(self, tmp_path: Path) -> None:
        base_dir = tmp_path / "sandbox"
        save_directory = base_dir / "nested" / "dir"

        local_path = await save_issue_attachment_file(
            b"inside",
            issue_id="TEST-1",
            attachment_id="1",
            file_name="file.txt",
            save_directory=str(save_directory),
            attachments_base_dir=base_dir,
        )

        assert local_path.is_relative_to(base_dir.resolve())
        assert local_path.read_bytes() == b"inside"

    @pytest.mark.parametrize(
        "save_directory",
        [
            "../outside",
            "/tmp/tracker-attachments-outside",
            "~/.config",
            "nested/../../outside",
        ],
        ids=[
            "parent_relative",
            "absolute_outside",
            "tilde_path",
            "traversal_after_resolve",
        ],
    )
    async def test_rejects_path_outside_base(
        self,
        tmp_path: Path,
        save_directory: str,
    ) -> None:
        base_dir = tmp_path / "sandbox"
        base_dir.mkdir(parents=True)

        with pytest.raises(ValueError, match="save_directory must be inside"):
            await save_issue_attachment_file(
                b"x",
                issue_id="TEST-1",
                attachment_id="1",
                file_name="file.txt",
                save_directory=save_directory,
                attachments_base_dir=base_dir,
            )

    async def test_wraps_oserror_from_mkdir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        base_dir = tmp_path / "sandbox"

        def _raise_oserror(self: Path, *args: object, **kwargs: object) -> None:
            raise OSError(13, "Permission denied")

        monkeypatch.setattr(Path, "mkdir", _raise_oserror)

        with pytest.raises(ValueError, match="Failed to create save directory"):
            await save_issue_attachment_file(
                b"x",
                issue_id="TEST-1",
                attachment_id="1",
                file_name="file.txt",
                save_directory=str(base_dir),
                attachments_base_dir=base_dir,
            )
