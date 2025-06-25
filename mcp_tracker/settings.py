from typing import Annotated, Any, Literal

from aiocache import Cache
from aiocache.serializers import PickleSerializer
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    host: str = "0.0.0.0"
    port: int = 8001
    transport: Literal["stdio", "sse"] = "stdio"
    tracker_token: str
    tracker_cloud_org_id: str | None = None
    tracker_org_id: str | None = None
    tracker_limit_queues: Annotated[list[str] | None, NoDecode] = None
    cache_enabled: bool = False
    cache_redis_endpoint: str = "localhost"
    cache_redis_port: int = 6379
    cache_redis_db: int = 0
    cache_redis_ttl: int | None = 3600

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
