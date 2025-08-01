from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession

from mcp_tracker.settings import Settings
from mcp_tracker.tracker.custom.client import TrackerClient


@pytest.fixture
def mock_settings() -> Settings:
    """Provide mock settings for testing."""
    return Settings(
        tracker_token="test-token",
        tracker_cloud_org_id="test-org-123",
        tracker_api_base_url="https://api.tracker.yandex.net",
        tools_cache_enabled=False,
        oauth_enabled=False,
    )


@pytest.fixture
async def mock_session() -> AsyncGenerator[AsyncMock, None]:
    """Provide a mock aiohttp ClientSession."""
    session = AsyncMock(spec=ClientSession)
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    yield session


@pytest.fixture
async def mock_tracker_client(
    mock_settings: Settings, mock_session: AsyncMock
) -> AsyncGenerator[TrackerClient, None]:
    """Provide a mock tracker client."""
    with patch("aiohttp.ClientSession", return_value=mock_session):
        client = TrackerClient(
            base_url=mock_settings.tracker_api_base_url,
            token=mock_settings.tracker_token,
            cloud_org_id=mock_settings.tracker_cloud_org_id,
            org_id=mock_settings.tracker_org_id,
        )
        yield client
        await client.close()
