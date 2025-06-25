from typing import Any, TypeVar

from mcp.types import TextContent
from pydantic import BaseModel, RootModel

T = TypeVar("T")


def dump_json_list(items: list[T], indent: int | None = 2) -> str:
    return RootModel(items).model_dump_json(indent=indent, exclude_none=True)


def dump_list(items: list[T]) -> dict[str, Any]:
    return RootModel(items).model_dump(exclude_none=True)


def prepare_text_content(
    obj: dict[str, Any] | list[Any] | BaseModel | str, indent: int | None = None
) -> TextContent:
    if isinstance(obj, list):
        content = dump_json_list(obj, indent=indent)
    elif isinstance(obj, dict):
        content = RootModel(obj).model_dump_json(indent=indent)
    elif isinstance(obj, BaseModel):
        content = obj.model_dump_json(indent=indent, exclude_none=True)
    elif isinstance(obj, str):
        content = obj
    else:
        raise TypeError(
            f"Unsupported type {type(obj)} for content preparation. "
            "Expected list, BaseModel, or str."
        )

    return TextContent(
        type="text",
        text=content,
    )
