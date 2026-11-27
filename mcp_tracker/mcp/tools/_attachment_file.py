"""Stream files within the local attachment directory."""

import os
import re
import stat
import sys
from collections.abc import AsyncIterable, AsyncIterator, Iterator
from contextlib import (
    AsyncExitStack,
    ExitStack,
    asynccontextmanager,
    contextmanager,
    suppress,
)
from pathlib import Path, PureWindowsPath
from uuid import uuid4

import aiofiles
from anyio import CancelScope, to_thread
from anyio.lowlevel import checkpoint_if_cancelled

from mcp_tracker.mcp.errors import TrackerError

if sys.platform == "win32":
    from mcp_tracker.mcp.tools._attachment_file_windows import open_file, pin_directory


MAX_ATTACHMENT_SIZE = 128 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


def attachment_path(file_path: str) -> PureWindowsPath:
    # Parse both separators on every platform and reject drive-relative paths,
    # UNC paths, alternate streams and Windows components subject to trimming.
    path = PureWindowsPath(file_path)
    if (
        path.anchor
        or not path.parts
        or any(
            part == ".."
            or part.endswith((".", " "))
            or ":" in part
            or any(ord(char) < 32 for char in part)
            for part in path.parts
        )
    ):
        raise TrackerError("Pass a relative file path inside the upload directory.")
    return path


@contextmanager
def _open_directory(path: Path) -> Iterator[int | None]:
    if sys.platform == "win32":
        with pin_directory(path):
            yield None
        return

    # Open each component relative to its parent and refuse symlinks at
    # every step. All writes and cleanup use the resulting directory handle.
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        yield directory
    finally:
        os.close(directory)


def _open_file(root: Path, parts: tuple[str, ...], flags: int) -> int:
    if sys.platform == "win32":
        return open_file(root, parts, flags)

    with _open_directory(root.joinpath(*parts[:-1])) as directory:
        # Opening a FIFO for inspection must not block.
        return os.open(
            parts[-1], flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )


@asynccontextmanager
async def open_attachment(
    root: Path, path: PureWindowsPath
) -> AsyncIterator[AsyncIterator[bytes]]:
    def opener(_name: str, flags: int) -> int:
        return _open_file(root, path.parts, flags)

    # Open through aiofiles so both the descriptor walk and the reads run off
    # the event loop. Use a relative name even in the file object's repr.
    async with AsyncExitStack() as stack:
        try:
            file = await stack.enter_async_context(
                aiofiles.open(path.as_posix(), "rb", opener=opener)
            )
            info = os.fstat(file.fileno())
        except (OSError, ValueError, RuntimeError):
            raise TrackerError(
                "Could not open the file in the upload directory."
            ) from None
        if not stat.S_ISREG(info.st_mode) or info.st_nlink > 1:
            raise TrackerError("Pass a regular file in the upload directory.")
        if info.st_size > MAX_ATTACHMENT_SIZE:
            raise TrackerError(
                f"The file exceeds the {MAX_ATTACHMENT_SIZE // 1024 // 1024} MiB upload limit."
            )

        async def chunks() -> AsyncIterator[bytes]:
            remaining = info.st_size
            try:
                while remaining:
                    chunk = await file.read(min(remaining, CHUNK_SIZE))
                    if not chunk:
                        raise TrackerError("The file changed during upload.")
                    remaining -= len(chunk)
                    yield chunk
                if await file.read(1):
                    raise TrackerError("The file changed during upload.")
            except OSError:
                raise TrackerError("Could not read the file during upload.") from None

        yield chunks()


@contextmanager
def _local_save_errors() -> Iterator[None]:
    try:
        yield
    except (OSError, ValueError):
        raise TrackerError(
            "Could not save the attachment in the local attachment directory."
        ) from None


async def save_attachment(
    root: Path,
    original_name: str,
    chunks: AsyncIterable[bytes],
) -> tuple[str, int]:
    suffix = PureWindowsPath(original_name).suffix
    if re.fullmatch(r"\.[A-Za-z0-9]{1,12}", suffix) is None:
        suffix = ""
    # The suffix is the only part borrowed from the original filename.
    basename = uuid4().hex
    file_path = f"{basename}{suffix}"
    partial_name = f".{basename}.part"

    with ExitStack() as stack:
        with _local_save_errors():
            directory = stack.enter_context(_open_directory(root))
            partial = root / partial_name if directory is None else Path(partial_name)
            destination = root / file_path if directory is None else Path(file_path)

            def opener(name: str, flags: int) -> int:
                return os.open(name, flags, 0o600, dir_fd=directory)

            file = open(partial, "xb", opener=opener)

        try:
            size = 0
            try:
                async for chunk in chunks:
                    with _local_save_errors():
                        # Wait for writes already running in the worker before closing.
                        size += await to_thread.run_sync(file.write, chunk)
            finally:
                with CancelScope(shield=True), _local_save_errors():
                    await to_thread.run_sync(file.close)

            await checkpoint_if_cancelled()
            with _local_save_errors():
                if sys.platform == "win32":
                    os.rename(partial, destination)
                else:
                    # Publish the complete file without replacing an existing name.
                    os.link(
                        partial,
                        destination,
                        src_dir_fd=directory,
                        dst_dir_fd=directory,
                        follow_symlinks=False,
                    )
        finally:
            with _local_save_errors(), suppress(FileNotFoundError):
                os.unlink(partial, dir_fd=directory)

    return file_path, size
