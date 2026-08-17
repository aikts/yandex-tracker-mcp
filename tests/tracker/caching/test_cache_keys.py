from dataclasses import fields
from typing import Any
from unittest.mock import AsyncMock

import pytest

from mcp_tracker.tracker.caching.client import make_cached_protocols
from mcp_tracker.tracker.proto.common import YandexAuth, secret_fingerprint
from mcp_tracker.tracker.proto.types.users import User

SECRET_TOKEN = "y0_AgAAAAB_SECRET_USER_TOKEN"


class TestSecretFingerprint:
    def test_fingerprint_hides_the_secret(self) -> None:
        fingerprint = secret_fingerprint(SECRET_TOKEN)

        assert SECRET_TOKEN not in fingerprint
        assert fingerprint == "sha256:97418b749fd91151dd9ffd0e4be500b6"

    def test_fingerprint_of_none(self) -> None:
        assert secret_fingerprint(None) == "none"


class TestYandexAuthRepr:
    """The repr is what aiocache turns into a cache key, so it is load-bearing."""

    def test_repr_hides_the_token(self) -> None:
        auth = YandexAuth(token=SECRET_TOKEN, org_id="org-1")

        assert SECRET_TOKEN not in repr(auth)
        assert secret_fingerprint(SECRET_TOKEN) in repr(auth)

    def test_repr_covers_every_field(self) -> None:
        auth = YandexAuth(token=SECRET_TOKEN, cloud_org_id="cloud-1", org_id="org-1")

        for field in fields(auth):
            assert f"{field.name}=" in repr(auth)
        assert "cloud-1" in repr(auth)
        assert "org-1" in repr(auth)

    @pytest.mark.parametrize(
        "other_auth",
        [
            YandexAuth(token="another-token", org_id="org-1"),
            YandexAuth(token=None, org_id="org-1"),
            YandexAuth(token=SECRET_TOKEN, org_id="org-2"),
            YandexAuth(token=SECRET_TOKEN, cloud_org_id="cloud-1", org_id="org-1"),
        ],
    )
    def test_different_auth_renders_differently(self, other_auth: YandexAuth) -> None:
        assert repr(YandexAuth(token=SECRET_TOKEN, org_id="org-1")) != repr(other_auth)

    def test_token_is_still_accessible(self) -> None:
        assert YandexAuth(token=SECRET_TOKEN).token == SECRET_TOKEN


class TestCachedProtocolKeys:
    @pytest.fixture
    def mock_original(self) -> AsyncMock:
        original = AsyncMock()
        original.user_get.return_value = User(
            uid=123, login="test_user", display="Test User"
        )
        return original

    @pytest.fixture
    def caching_users_protocol(self, mock_original: AsyncMock) -> Any:
        cache_collection = make_cached_protocols({"ttl": 300, "noself": True})
        return cache_collection.users(mock_original)

    async def test_cache_key_does_not_contain_the_token(
        self, caching_users_protocol: Any
    ) -> None:
        await caching_users_protocol.user_get(
            "cache-key-user-1", auth=YandexAuth(token=SECRET_TOKEN, org_id="org-1")
        )
        keys = list(type(caching_users_protocol).user_get.cache._cache)

        assert keys
        assert all(SECRET_TOKEN not in key for key in keys)

    async def test_same_token_hits_cache(
        self, caching_users_protocol: Any, mock_original: AsyncMock
    ) -> None:
        await caching_users_protocol.user_get(
            "cache-key-user-2", auth=YandexAuth(token=SECRET_TOKEN, org_id="org-1")
        )
        await caching_users_protocol.user_get(
            "cache-key-user-2", auth=YandexAuth(token=SECRET_TOKEN, org_id="org-1")
        )

        mock_original.user_get.assert_called_once()

    async def test_different_tokens_do_not_share_cache(
        self, caching_users_protocol: Any, mock_original: AsyncMock
    ) -> None:
        await caching_users_protocol.user_get(
            "cache-key-user-3", auth=YandexAuth(token=SECRET_TOKEN, org_id="org-1")
        )
        await caching_users_protocol.user_get(
            "cache-key-user-3", auth=YandexAuth(token="another-token", org_id="org-1")
        )

        assert mock_original.user_get.call_count == 2
