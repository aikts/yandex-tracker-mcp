from typing import Annotated, Any, Literal

from aiocache import Cache
from aiocache.serializers import PickleSerializer
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        str_strip_whitespace=True,
    )

    host: str = "0.0.0.0"
    port: int = 8000
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    tracker_api_base_url: str = "https://api.tracker.yandex.net"
    tracker_token: str | None = None
    tracker_iam_token: str | None = None
    tracker_cloud_org_id: str | None = None
    tracker_org_id: str | None = None
    tracker_limit_queues: Annotated[list[str] | None, NoDecode] = None
    tracker_read_only: bool = False

    tracker_sa_key_id: str | None = None
    tracker_sa_service_account_id: str | None = None
    tracker_sa_private_key: str | None = None

    redis_endpoint: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_pool_max_size: int = 10

    tools_cache_enabled: bool = False
    tools_cache_redis_ttl: int | None = 3600

    oauth_enabled: bool = False
    oauth_store: Literal["redis", "memory"] = "memory"
    oauth_server_url: AnyHttpUrl = AnyHttpUrl("https://oauth.yandex.ru")
    oauth_use_scopes: bool = True
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None
    oauth_token_type: Literal["Bearer", "OAuth"] | None = None
    mcp_server_public_url: AnyHttpUrl | None = None

    @model_validator(mode="after")
    def validate_settings(self):
        if self.oauth_enabled:
            if not self.oauth_client_id or not self.oauth_client_secret:
                raise ValueError(
                    "client_id and client_secret must be set when oauth_enabled is True"
                )
            if not self.oauth_server_url:
                raise ValueError(
                    "auth_server_url must be set when oauth_enabled is True"
                )
            if not self.mcp_server_public_url:
                raise ValueError("server_url must be set when oauth_enabled is True")

        else:
            if not self.tracker_token and not self.tracker_iam_token:
                if self.tracker_sa_key_id is None:
                    raise ValueError(
                        "tracker_token or tracker_iam_token or tracker_sa_* must be set when oauth_enabled is False"
                    )
                else:
                    if (
                        self.tracker_sa_service_account_id is None
                        or self.tracker_sa_private_key is None
                    ):
                        raise ValueError(
                            "tracker_sa_key_id, tracker_sa_service_account_id and tracker_sa_private_key must be set when configuring service account access"
                        )

        return self

    @field_validator("tracker_limit_queues", mode="before")
    @classmethod
    def decode_numbers(cls, v: str | None) -> list[str] | None:
        if v is None:
            return None
        if not isinstance(v, str):
            raise TypeError(f"Expected str or None, got {type(v)}")

        return [x.strip() for x in v.split(",") if x.strip()]

    def cache_kwargs(self) -> dict[str, Any]:
        return {
            "cache": Cache.REDIS,
            "endpoint": self.redis_endpoint,
            "port": self.redis_port,
            "db": self.redis_db,
            "password": self.redis_password,
            "pool_max_size": self.redis_pool_max_size,
            "serializer": PickleSerializer(),
            "noself": True,
            "ttl": self.tools_cache_redis_ttl,
        }
