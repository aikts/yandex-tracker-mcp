import asyncio
import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from mcp.client.session import ClientSession
from mcp.types import BlobResourceContents, EmbeddedResource, ImageContent, TextContent

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.server import create_mcp_server, make_tracker_lifespan
from mcp_tracker.mcp.tools._attachment_file import save_attachment
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.errors import AttachmentTooLarge
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import AttachmentDownload, IssueAttachment
from tests.mcp.conftest import get_tool_result_content

PARAMS = {"issue_id": "TEST-123", "attachment_id": "17"}


@pytest.fixture
def mock_download(mock_issues_protocol: AsyncMock) -> AttachmentDownload:
    async def chunks() -> AsyncIterator[bytes]:
        yield b"first"
        yield b" second"

    download = AttachmentDownload(
        IssueAttachment.model_construct(id="17", name="source.png"),
        "image/png",
        chunks(),
    )

    @asynccontextmanager
    async def open_download(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[AttachmentDownload]:
        yield download

    mock_issues_protocol.issue_open_attachment.side_effect = open_download
    return download


@pytest.mark.parametrize(
    ("mime", "payload", "representation"),
    [
        ("image/png", b"\x89PNG\x00", "image"),
        ('text/plain; charset="windows-1251"', "Привет".encode("cp1251"), "text"),
        ("application/octet-stream", b"\xff\x00", "blob"),
    ],
)
async def test_inline_content(
    client_session: ClientSession,
    mock_issues_protocol: AsyncMock,
    mime: str,
    payload: bytes,
    representation: str,
) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield payload

    @asynccontextmanager
    async def open_download(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[AttachmentDownload]:
        yield AttachmentDownload(
            IssueAttachment.model_construct(id="17", name="fixture"),
            mime,
            chunks(),
        )

    mock_issues_protocol.issue_open_attachment.side_effect = open_download
    result = await client_session.call_tool("issue_get_attachment_content", PARAMS)

    assert not result.isError
    assert result.structuredContent is None
    _, content = result.content
    if representation == "text":
        assert isinstance(content, TextContent)
        assert content.text == "Привет"
    elif representation == "image":
        assert isinstance(content, ImageContent)
        assert base64.b64decode(content.data) == payload
    else:
        assert isinstance(content, EmbeddedResource)
        assert isinstance(content.resource, BlobResourceContents)
        assert base64.b64decode(content.resource.blob) == payload

    mock_issues_protocol.issue_open_attachment.assert_called_once_with(
        "TEST-123",
        "17",
        max_bytes=10 * 1024 * 1024,
        limit_setting="TRACKER_ATTACHMENT_INLINE_MAX_BYTES",
        auth=YandexAuth(),
    )


@pytest.mark.parametrize(
    "tool", ["issue_get_attachment_content", "issue_download_attachment_local"]
)
async def test_download_respects_queue_allow_list(
    client_session_with_limits: ClientSession,
    mock_issues_protocol: AsyncMock,
    tool: str,
) -> None:
    result = await client_session_with_limits.call_tool(tool, PARAMS)
    assert result.isError
    mock_issues_protocol.issue_open_attachment.assert_not_called()


async def test_local_download_path_can_be_uploaded(
    client_session: ClientSession,
    mock_issues_protocol: AsyncMock,
    mock_download: AttachmentDownload,
    upload_root: Path,
) -> None:
    result = await client_session.call_tool("issue_download_attachment_local", PARAMS)
    assert not result.isError
    content = get_tool_result_content(result)
    path = content["file_path"]
    assert not Path(path).is_absolute()
    assert content["original_name"] == mock_download.metadata.name
    assert content["mime_type"] == "image/png"
    assert content["size"] == 12
    assert (upload_root / path).read_bytes() == b"first second"
    mock_issues_protocol.issue_open_attachment.assert_called_once_with(
        "TEST-123",
        "17",
        max_bytes=50 * 1024 * 1024,
        limit_setting="TRACKER_ATTACHMENT_DOWNLOAD_MAX_BYTES",
        auth=YandexAuth(),
    )

    async def receive(
        issue_id: str, *, content: AsyncIterator[bytes], filename: str, auth: YandexAuth
    ) -> IssueAttachment:
        assert issue_id == "TEST-123"
        assert filename == path
        assert b"".join([chunk async for chunk in content]) == b"first second"
        return mock_download.metadata

    mock_issues_protocol.issue_add_attachment.side_effect = receive
    uploaded = await client_session.call_tool(
        "issue_add_attachment_local", {"issue_id": "TEST-123", "file_path": path}
    )
    assert not uploaded.isError


@pytest.mark.parametrize(
    "error",
    [
        AttachmentTooLarge(1, "TRACKER_ATTACHMENT_DOWNLOAD_MAX_BYTES"),
        asyncio.CancelledError(),
    ],
)
async def test_partial_download_is_removed(
    upload_root: Path, error: BaseException
) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b"first"
        raise error

    with pytest.raises(type(error)):
        await save_attachment(upload_root, "TEST-123", "17", "file.png", chunks())

    assert list(upload_root.iterdir()) == []


async def test_symlink_cannot_redirect_local_download(
    upload_root: Path, tmp_path: Path
) -> None:
    from_path = upload_root.with_name("actual")
    upload_root.rename(from_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        upload_root.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks are unavailable")
    with pytest.raises(TrackerError, match="Could not save"):
        await save_attachment(upload_root, "TEST-123", "17", "file.png", mock_chunks())

    assert list(outside.iterdir()) == []


async def mock_chunks() -> AsyncIterator[bytes]:
    yield b"data"


async def test_download_temp_directory_lives_until_shutdown() -> None:
    settings = Settings.model_construct(
        tracker_attachment_download_enabled=True,
        tracker_token="token",
        tracker_org_id="org",
    )
    async with make_tracker_lifespan(settings)(create_mcp_server(settings)) as app:
        directory = app.temporary_attachments_dir
        assert directory is not None
        assert directory.is_dir()
        (directory / "downloaded").write_bytes(b"bytes")

    assert not directory.exists()
