from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseTrackerEntity(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )


def none_excluder(v: Any) -> bool:
    return v is None


NoneExcludedField = Field(None, exclude_if=none_excluder)
