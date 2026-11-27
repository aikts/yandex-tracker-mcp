"""Win32 operations for keeping local attachments inside the configured directory.

POSIX can open children relative to verified directory descriptors. Windows
path-based opens need the handle checks and rename protection below to cover
changes between path validation and use.
"""

import ctypes
import msvcrt
import os
import stat
import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from ctypes import wintypes
from pathlib import Path

if sys.platform == "win32":
    FILE_READ_ATTRIBUTES = 0x80
    FILE_SHARE_READ = 0x01
    FILE_SHARE_WRITE = 0x02
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

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
    def pin_directory(directory: Path) -> Iterator[None]:
        # The writer needs the same directory to stay in place through creation,
        # publication, and cleanup. Without FILE_SHARE_DELETE, Windows denies
        # renames and deletion while these handles, including ancestors, are open.
        # OPEN_REPARSE_POINT lets us inspect a junction or symlink without following it.
        with ExitStack() as stack:
            for path in (*reversed(directory.parents), directory):
                handle = _create_file(
                    str(path),
                    FILE_READ_ATTRIBUTES,
                    FILE_SHARE_READ | FILE_SHARE_WRITE,
                    None,
                    OPEN_EXISTING,
                    FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
                    None,
                )
                if handle is None or handle == INVALID_HANDLE_VALUE:
                    raise OSError
                stack.callback(_close_handle, handle)
                if (
                    os.lstat(path).st_file_attributes
                    & stat.FILE_ATTRIBUTE_REPARSE_POINT
                ):
                    raise ValueError
                _verify_windows_handle(handle, path)
            yield

    def open_file(root: Path, parts: tuple[str, ...], flags: int) -> int:
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
        # A directory can be replaced between resolve() and open(). Check the
        # path of the actual handle before the caller reads any bytes.
        try:
            _verify_windows_handle(msvcrt.get_osfhandle(fd), resolved)
        except BaseException:
            os.close(fd)
            raise
        return fd
