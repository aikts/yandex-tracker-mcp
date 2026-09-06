"""`main()` dispatches on `TRANSPORT` with the options each transport takes.

`MCPServer.run()` is overloaded per transport and an option the transport does
not take (`host` on stdio, say) is a `TypeError` at startup - which no other
test would see, since the tests connect in-process and never call `run()`.
"""

import importlib
import sys
from types import ModuleType
from typing import Any
from unittest.mock import Mock

import pytest

from tests.mcp.conftest import create_test_settings


@pytest.fixture
def main_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """`mcp_tracker.__main__`, imported against a minimal environment.

    The module builds `Settings()` and the server at import time, so it is
    imported here rather than at the top of the file, with the required
    settings in the environment and never from a stray `.env`.
    """
    monkeypatch.setenv("TRACKER_TOKEN", "test-token")
    monkeypatch.setenv("TRACKER_ORG_ID", "test-org")
    monkeypatch.delenv("TRACKER_CLOUD_ORG_ID", raising=False)
    monkeypatch.delitem(sys.modules, "mcp_tracker.__main__", raising=False)
    module = importlib.import_module("mcp_tracker.__main__")
    monkeypatch.delitem(sys.modules, "mcp_tracker.__main__", raising=False)
    return module


@pytest.mark.parametrize(
    ("transport", "expected_kwargs"),
    [
        ("stdio", {"transport": "stdio"}),
        ("sse", {"transport": "sse", "host": "127.0.0.1", "port": 9000}),
        (
            "streamable-http",
            {
                "transport": "streamable-http",
                "host": "127.0.0.1",
                "port": 9000,
                "stateless_http": True,
                "json_response": True,
            },
        ),
    ],
    ids=["stdio", "sse", "streamable-http"],
)
def test_main_runs_the_configured_transport(
    main_module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    transport: str,
    expected_kwargs: dict[str, Any],
) -> None:
    settings = create_test_settings().model_copy(
        update={"transport": transport, "host": "127.0.0.1", "port": 9000}
    )
    run = Mock()
    monkeypatch.setattr(main_module, "settings", settings)
    monkeypatch.setattr(main_module.mcp, "run", run)

    main_module.main()

    run.assert_called_once_with(**expected_kwargs)
