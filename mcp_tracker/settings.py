from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    port: int = 8001
    transport: Literal["stdio", "sse"] = "stdio"
    tracker_token: str
    tracker_cloud_org_id: str | None = None
    tracker_org_id: str | None = None
