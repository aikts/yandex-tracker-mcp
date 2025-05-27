from typing import Any

from mcp.types import TextContent
from pydantic import BaseModel, RootModel


def dump_json_list[T](items: list[T], indent: int | None = 2) -> str:
    return RootModel(items).model_dump_json(indent=indent, exclude_none=True)


def dump_list[T](items: list[T]) -> dict[str, Any]:
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
