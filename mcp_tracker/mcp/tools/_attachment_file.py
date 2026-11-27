"""Stream files within the local attachment directory."""

import os
import re
import stat
import sys
from collections.abc import AsyncIterable, AsyncIterator, Iterator
from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from pathlib import Path, PureWindowsPath
from uuid import uuid4

import aiofiles

from mcp_tracker.mcp.errors import TrackerError

if sys.platform == "win32":
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _get_final_path = kernel32.GetFinalPathNameByHandleW
    _get_final_path.argtypes = (
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    _get_final_path.restype = wintypes.DWORD
    _create_file = kernel32.CreateFileW
    _create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    _create_file.restype = wintypes.HANDLE
    _close_handle = kernel32.CloseHandle
    _close_handle.argtypes = (wintypes.HANDLE,)
    _close_handle.restype = wintypes.BOOL

    def _verify_windows_handle(handle: int, path: Path) -> None:
        buffer = ctypes.create_unicode_buffer(32768)
        length = _get_final_path(handle, buffer, len(buffer), 0)
        if not 0 < length < len(buffer):
            raise ValueError
        final = buffer.value
        if final.startswith("\\\\?\\UNC\\"):
            final = "\\\\" + final[8:]
        elif final.startswith("\\\\?\\"):
            final = final[4:]
        opened = Path(final)
        if (
            opened.anchor.casefold() != path.anchor.casefold()
            or opened.parts[1:] != path.parts[1:]
        ):
            raise ValueError

    @contextmanager
    def _pin_windows_directory(directory: Path) -> Iterator[None]:
        # Deny delete sharing on each ancestor so Windows keeps the verified
        # path in place throughout creation, publication, and cleanup.
        with ExitStack() as stack:
            for path in (*reversed(directory.parents), directory):
                handle = _create_file(
                    str(path),
                    0x80,  # FILE_READ_ATTRIBUTES
                    0x03,  # FILE_SHARE_READ | FILE_SHARE_WRITE
                    None,
                    3,  # OPEN_EXISTING
                    0x02200000,  # FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT
                    None,
                )
                if handle is None or handle == ctypes.c_void_p(-1).value:
                    raise OSError
                stack.callback(_close_handle, handle)
                if (
                    os.lstat(path).st_file_attributes
                    & stat.FILE_ATTRIBUTE_REPARSE_POINT
                ):
                    raise ValueError
                _verify_windows_handle(handle, path)
            yield

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
            _verify_windows_handle(msvcrt.get_osfhandle(fd), resolved)
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


@contextmanager
def _open_directory(path: Path) -> Iterator[int | None]:
    if sys.platform == "win32":
        with _pin_windows_directory(path):
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
        return _windows_open(root, parts, flags)

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


async def save_attachment(
    root: Path,
    issue_id: str,
    attachment_id: str,
    original_name: str,
    chunks: AsyncIterable[bytes],
) -> tuple[str, int]:
    suffix = PureWindowsPath(original_name).suffix
    if re.fullmatch(r"\.[A-Za-z0-9]{1,12}", suffix) is None:
        suffix = ""
    # Both identifiers have already been validated. The suffix is the only
    # part borrowed from the original filename.
    basename = f"{issue_id}-{attachment_id}-{uuid4().hex}"
    file_path = f"{basename}{suffix}"
    partial_name = f".{basename}.part"

    try:
        with _open_directory(root) as directory:
            partial = root / partial_name if directory is None else Path(partial_name)
            destination = root / file_path if directory is None else Path(file_path)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if sys.platform == "win32":
                flags |= os.O_BINARY
            fd = os.open(partial, flags, 0o600, dir_fd=directory)
            try:
                size = 0
                try:
                    async with aiofiles.open(fd, "wb", closefd=False) as file:
                        async for chunk in chunks:
                            size += await file.write(chunk)
                finally:
                    os.close(fd)

                # Publish only after the stream and file close complete.
                # POSIX rename would overwrite an existing destination.
                if sys.platform == "win32":
                    os.rename(partial, destination)
                else:
                    os.link(
                        partial,
                        destination,
                        src_dir_fd=directory,
                        dst_dir_fd=directory,
                        follow_symlinks=False,
                    )
            finally:
                try:
                    os.unlink(partial, dir_fd=directory)
                except FileNotFoundError:
                    pass

    except (OSError, ValueError, RuntimeError):
        raise TrackerError(
            "Could not save the attachment in the local attachment directory."
        ) from None

    return file_path, size
