from pydantic import Field, BaseModel, ConfigDict


class BaseTrackerEntity(BaseModel):
    self_: str = Field(alias="self")

    model_config = ConfigDict(
        extra="allow",
    )


