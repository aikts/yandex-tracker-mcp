from pydantic import BaseModel, ConfigDict, Field


class BaseTrackerEntity(BaseModel):
    self_: str = Field(alias="self", exclude=True)

    model_config = ConfigDict(
        extra="allow",
    )
