import asyncio
import base64
import errno
import io
import subprocess
import sys
import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import anyio
import pytest
from aiohttp import ClientOSError
from mcp.client.session import ClientSession
from mcp.types import BlobResourceContents, EmbeddedResource, ImageContent, TextContent

from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.tools import _attachment_file
from mcp_tracker.mcp.tools._attachment_file import (
    attachment_path,
    open_attachment,
    save_attachment,
)
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
        mime_type="image/png",
        charset=None,
        chunks=chunks(),
    )

    @asynccontextmanager
    async def open_download(
        *_args: object, **_kwargs: object
    ) -> AsyncIterator[AttachmentDownload]:
        yield download

    mock_issues_protocol.issue_open_attachment.side_effect = open_download
    return download


@pytest.mark.parametrize(
    ("mime", "charset", "payload", "representation"),
    [
        ("image/png", None, b"\x89PNG\x00", "image"),
        ("text/plain", "windows-1251", "Привет".encode("cp1251"), "text"),
        ("application/octet-stream", None, b"\xff\x00", "blob"),
    ],
)
async def test_inline_content(
    client_session: ClientSession,
    mock_issues_protocol: AsyncMock,
    mime: str,
    charset: str | None,
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
            mime_type=mime,
            charset=charset,
            chunks=chunks(),
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
        max_bytes=1024 * 1024,
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
        max_bytes=128 * 1024 * 1024,
        timeout=300.0,
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
        AttachmentTooLarge(1),
        ClientOSError(errno.ECONNRESET, "connection reset"),
        asyncio.CancelledError(),
    ],
)
async def test_partial_download_is_removed(
    upload_root: Path, error: BaseException
) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b"first"
        raise error

    with pytest.raises(type(error)) as caught:
        await save_attachment(upload_root, "file.png", chunks())

    assert caught.value is error
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
        await save_attachment(upload_root, "file.png", mock_chunks())

    assert list(outside.iterdir()) == []


async def mock_chunks() -> AsyncIterator[bytes]:
    yield b"data"


async def test_cancellation_waits_for_the_inflight_disk_write(
    upload_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop = asyncio.get_running_loop()
    write_started = anyio.Event()
    release_write = threading.Event()
    order: list[str] = []
    cancel_scope = anyio.CancelScope()

    def open_slow_file(
        path: Path, mode: str, *, opener: Callable[[str, int], int]
    ) -> SimpleNamespace:
        file = io.FileIO(path, mode, opener=opener)

        def write(data: bytes) -> int:
            loop.call_soon_threadsafe(write_started.set)
            assert release_write.wait(timeout=5)
            count = file.write(data)
            order.append("written")
            return count

        def close() -> None:
            order.append("closed")
            file.close()

        return SimpleNamespace(write=write, close=close)

    async def download() -> None:
        with cancel_scope:
            await save_attachment(upload_root, "file.png", mock_chunks())
            pytest.fail("A cancelled download published a file")

    monkeypatch.setattr(_attachment_file, "open", open_slow_file, raising=False)
    with anyio.fail_after(5):
        async with anyio.create_task_group() as group:
            group.start_soon(download)
            try:
                await write_started.wait()
                cancel_scope.cancel()
                await anyio.wait_all_tasks_blocked()
                assert order == []
            finally:
                release_write.set()
    assert order == ["written", "closed"]
    assert list(upload_root.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="NTFS junctions require Windows")
@pytest.mark.parametrize("operation", ["upload", "download"])
async def test_junction_cannot_redirect_local_files(
    upload_root: Path, tmp_path: Path, operation: str
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = upload_root / "junction"
    subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
        check=True,
        capture_output=True,
    )

    if operation == "upload":
        (outside / "fixture.txt").write_bytes(b"fixture")
        with pytest.raises(TrackerError, match="Could not open"):
            async with open_attachment(
                upload_root, attachment_path("junction/fixture.txt")
            ):
                pytest.fail("Upload opened a file through a junction")
    else:
        with pytest.raises(TrackerError, match="Could not save"):
            await save_attachment(link, "file.png", mock_chunks())
        assert list(outside.iterdir()) == []
