from typing import Protocol

from .types.fields import GlobalField


class FieldsProtocol(Protocol):
    async def get_global_fields(self) -> list[GlobalField]: ...


class FieldsProtocolWrap(FieldsProtocol):
    def __init__(self, original: FieldsProtocol):
        self._original = original
