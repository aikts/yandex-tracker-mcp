from typing import Annotated, Any, Literal

from aiocache import Cache
from aiocache.serializers import PickleSerializer
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    host: str = "0.0.0.0"
    port: int = 8000
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    tracker_base_url: str = "https://api.tracker.yandex.net"
    tracker_token: str | None = None
    tracker_cloud_org_id: str | None = None
    tracker_org_id: str | None = None
    tracker_limit_queues: Annotated[list[str] | None, NoDecode] = None
    cache_enabled: bool = False
    cache_redis_endpoint: str = "localhost"
    cache_redis_port: int = 6379
    cache_redis_db: int = 0
    cache_redis_ttl: int | None = 3600

    oauth_enabled: bool = False
    auth_server_url: AnyHttpUrl = AnyHttpUrl("https://oauth.yandex.ru")
    server_url: AnyHttpUrl = AnyHttpUrl(f"http://{host}:{port}")
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = None

    @model_validator(mode="after")
    def validate_settings(self):
        if not self.tracker_cloud_org_id and not self.tracker_org_id:
            raise ValueError(
                "Either tracker_cloud_org_id or tracker_org_id must be set"
            )
        if self.tracker_cloud_org_id and self.tracker_org_id:
            raise ValueError(
                "Only one of tracker_cloud_org_id or tracker_org_id can be set"
            )

        if self.oauth_enabled:
            if not self.oauth_client_id or not self.oauth_client_secret:
                raise ValueError(
                    "client_id and client_secret must be set when oauth_enabled is True"
                )
            if not self.auth_server_url:
                raise ValueError(
                    "auth_server_url must be set when oauth_enabled is True"
                )
            if not self.server_url:
                raise ValueError("server_url must be set when oauth_enabled is True")

        else:
            if not self.tracker_token:
                raise ValueError(
                    "tracker_token must be set when oauth_enabled is False"
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
            "endpoint": self.cache_redis_endpoint,
            "port": self.cache_redis_port,
            "db": self.cache_redis_db,
            "pool_max_size": 10,
            "serializer": PickleSerializer(),
            "noself": True,
            "ttl": self.cache_redis_ttl,
        }
