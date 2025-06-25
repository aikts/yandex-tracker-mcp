from typing import Any

from pydantic import BaseModel, Field

from mcp_tracker.tracker.proto.types.base import BaseTrackerEntity
from mcp_tracker.tracker.proto.types.refs import BaseReference


class FieldSchema(BaseModel):
    """Field schema/data type information"""

    type: str | None = None
    items: str | None = None
    required: bool | None = None


class SuggestProvider(BaseModel):
    type: str | None = None


class QueryProvider(BaseModel):
    type: str | None = None


class OptionsProvider(BaseModel):
    type: str | None = None
    values: Any | None = None


class CategoryRef(BaseReference):
    display: str | None = None


class GlobalField(BaseTrackerEntity):
    """Global field available in Yandex Tracker"""

    id: str
    name: str | None = None
    key: str | None = None
    version: int | None = None
    schema_: FieldSchema | None = Field(
        default=None, alias="schema", serialization_alias="schema"
    )
    readonly: bool | None = None
    options: bool | None = None
    suggest: bool | None = None
    type: str | None = None
    order: int | None = None
    suggestProvider: SuggestProvider | None = None
    optionsProvider: OptionsProvider | None = None
    queryProvider: QueryProvider | None = None
    category: CategoryRef | None = None


class LocalField(GlobalField):
    """Queue-specific local field"""

    description: str | None = None
