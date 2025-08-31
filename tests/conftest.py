from typing import AsyncGenerator

import pytest

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.proto.common import YandexAuth


@pytest.fixture
async def tracker_client() -> AsyncGenerator[TrackerClient, None]:
    """Create a TrackerClient with org_id for testing."""
    client = TrackerClient(
        token="test-token",
        org_id="test-org",
        base_url="https://api.tracker.yandex.net",
    )
    yield client
    await client.close()


@pytest.fixture
async def tracker_client_no_org() -> AsyncGenerator[TrackerClient, None]:
    """Create a TrackerClient without org_id for testing auth parameter."""
    client = TrackerClient(
        token="test-token",
        base_url="https://api.tracker.yandex.net",
    )
    yield client
    await client.close()


@pytest.fixture
def yandex_auth() -> YandexAuth:
    """YandexAuth with org_id for testing."""
    return YandexAuth(token="auth-token", org_id="auth-org")


@pytest.fixture
def yandex_auth_cloud() -> YandexAuth:
    """YandexAuth with cloud_org_id for testing."""
    return YandexAuth(token="auth-token", cloud_org_id="cloud-org")
