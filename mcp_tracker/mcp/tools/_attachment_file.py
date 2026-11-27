"""Open and stream a regular file from the configured upload directory."""

import os
import stat
import sys
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path, PureWindowsPath

import aiofiles

from mcp_tracker.mcp.errors import TrackerError

if sys.platform == "win32":
    import ctypes
    import msvcrt
    from ctypes import wintypes

    _get_final_path = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetFinalPathNameByHandleW
    _get_final_path.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    _get_final_path.restype = wintypes.DWORD

    def _windows_open(root: Path, parts: tuple[str, ...], flags: int) -> int:
        # Resolve before opening to reject devices and junctions. Compare the
        # canonical directory names exactly for case-sensitive NTFS directories.
        path = root.joinpath(*parts)
        resolved = path.resolve(strict=True)
        if (
            resolved != path
            or resolved.anchor.casefold() != root.anchor.casefold()
            or resolved.parts[1 : len(root.parts)] != root.parts[1:]
            or not resolved.is_file()
        ):
            raise ValueError
        fd = os.open(resolved, flags)
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            length = _get_final_path(msvcrt.get_osfhandle(fd), buffer, len(buffer), 0)
            if not 0 < length < len(buffer):
                raise ValueError
            final = buffer.value
            if final.startswith("\\\\?\\UNC\\"):
                final = "\\\\" + final[8:]
            elif final.startswith("\\\\?\\"):
                final = final[4:]
            opened = Path(final)
            if (
                opened.anchor.casefold() != resolved.anchor.casefold()
                or opened.parts[1:] != resolved.parts[1:]
            ):
                raise ValueError
        except BaseException:
            os.close(fd)
            raise
        return fd


MAX_ATTACHMENT_SIZE = 1024 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


def attachment_path(file_path: str) -> PureWindowsPath:
    # Parse both separators on every platform and reject drive-relative paths,
    # UNC paths, alternate streams and Windows components subject to trimming.
    path = PureWindowsPath(file_path)
    if (
        path.anchor
        or not path.parts
        or any(
            part.endswith((".", " "))
            or ":" in part
            or any(ord(char) < 32 for char in part)
            for part in path.parts
        )
    ):
        raise TrackerError("Pass a relative file path inside the upload directory.")
    return path


def _open_file(root: Path, parts: tuple[str, ...], flags: int) -> int:
    if sys.platform == "win32":
        return _windows_open(root, parts, flags)

    # Resolve each directory relative to its open parent descriptor. A symlink
    # substituted at any point is refused by the kernel, including at the file.
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(root.anchor, directory_flags)
    try:
        for part in (*root.parts[1:], *parts[:-1]):
            child = os.open(part, directory_flags, dir_fd=directory)
            os.close(directory)
            directory = child
        # Opening a FIFO for inspection must not block.
        return os.open(
            parts[-1], flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
    finally:
        os.close(directory)


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
