from pydantic import BaseModel, ConfigDict


class BaseTrackerEntity(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
