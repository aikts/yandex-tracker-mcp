import json
from typing import Any

from aiocache.serializers import BaseSerializer
from pydantic import BaseModel

from .crypto import FieldEncryptor


class PydanticJsonSerializer(BaseSerializer):
    """JSON serializer with Pydantic model support."""

    DEFAULT_ENCODING = "utf-8"

    def dumps(self, value: Any) -> bytes:  # ty: ignore[invalid-method-override]
        if isinstance(value, BaseModel):
            return value.model_dump_json().encode(self.encoding)
        return json.dumps(value, default=str).encode(self.encoding)  # ty: ignore[invalid-argument-type]

    def loads(self, value: str) -> Any:
        return json.loads(value) if value is not None else None


class EncryptedFieldSerializer(PydanticJsonSerializer):
    """Serializer that encrypts sensitive fields (token, client_secret)."""

    ENCRYPTED_FIELDS = frozenset({"token", "client_secret"})

    def __init__(self, encryptor: FieldEncryptor | None = None) -> None:
        super().__init__()
        self._encryptor = encryptor

    def dumps(self, value: Any) -> bytes:  # ty: ignore[invalid-method-override]
        data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
        if self._encryptor is not None and isinstance(data, dict):
            data = self._encrypt_fields(data)
        return json.dumps(data, default=str).encode(self.encoding)  # ty: ignore[invalid-argument-type]

    def loads(self, value: str) -> Any:
        if value is None:
            return None
        data = json.loads(value)
        if self._encryptor is not None and isinstance(data, dict):
            data = self._decrypt_fields(data)
        return data

    def _encrypt_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        result = data.copy()
        for field in self.ENCRYPTED_FIELDS:
            if field in result and result[field] is not None:
                result[field] = self._encryptor.encrypt(str(result[field]))  # type: ignore[union-attr]
        return result

    def _decrypt_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        result = data.copy()
        for field in self.ENCRYPTED_FIELDS:
            if field in result and result[field] is not None:
                result[field] = self._encryptor.decrypt(result[field])  # type: ignore[union-attr]
        return result
