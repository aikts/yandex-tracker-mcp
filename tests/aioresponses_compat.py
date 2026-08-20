"""Make aioresponses work with aiohttp >= 3.14.

aioresponses 0.7.9 still builds its fake response with the pre-3.14
``ClientResponse`` constructor. aiohttp 3.14 made ``stream_writer`` a required
keyword-only argument, so every mocked request dies with ``TypeError:
ClientResponse.__init__() missing 1 required keyword-only argument:
'stream_writer'``, and it also taught ``StreamReader`` to reach into the
protocol's parser for flow control once a body crosses the reader limit, which
aioresponses never sets.

Both fixes are upstream but unreleased (pnuckowski/aioresponses#292); the
``aioresponses_compat`` fixture in ``tests/conftest.py`` applies the same two
patches for the duration of a test and lets ``monkeypatch`` put the library
back afterwards. They are written to be no-ops once a release carries them, so
deleting this file is the only cleanup needed.
"""

import asyncio
import inspect
from typing import Any
from unittest.mock import Mock

import aioresponses.core
import pytest
from aiohttp import ClientResponse, StreamReader

_WANTS_STREAM_WRITER = "stream_writer" in inspect.signature(ClientResponse).parameters


class CompatClientResponse(ClientResponse):
    """``ClientResponse`` that fills in the argument aioresponses omits."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if _WANTS_STREAM_WRITER:
            # aioresponses passes ``writer=None`` to say the request is
            # already sent, and on that path aiohttp only reads
            # ``output_size`` off the stream writer.
            kwargs.setdefault("stream_writer", Mock(output_size=0))
        super().__init__(*args, **kwargs)


_stream_reader_factory = aioresponses.core.stream_reader_factory


def compat_stream_reader_factory(
    loop: asyncio.AbstractEventLoop | None = None,
) -> StreamReader:
    """Give the reader's protocol the parser its flow-control hooks call."""
    reader = _stream_reader_factory(loop)
    protocol = reader._protocol
    if getattr(protocol, "_parser", None) is None:
        parser = Mock()
        parser.feed_data.return_value = ([], False, b"")
        protocol._parser = parser
    return reader


def install(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch aioresponses for the lifetime of ``monkeypatch``.

    Both names are module-level defaults aioresponses reads at call time, so
    rebinding them is the whole patch — and undoing it restores the library.
    """
    monkeypatch.setattr(aioresponses.core, "ClientResponse", CompatClientResponse)
    monkeypatch.setattr(
        aioresponses.core, "stream_reader_factory", compat_stream_reader_factory
    )
