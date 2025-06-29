import json
from typing import Any

from aiocache.serializers import BaseSerializer
from pydantic import BaseModel


class PydanticJsonSerializer(BaseSerializer):
    """Custom serializer for Pydantic models using JSON."""

    DEFAULT_ENCODING = "utf-8"

    def dumps(self, value: Any) -> bytes:
        """Serialize a value to JSON bytes."""
        if isinstance(value, BaseModel):
            # Use Pydantic's model_dump_json for proper serialization
            return value.model_dump_json().encode(self.encoding)
        else:
            # For non-Pydantic objects, use standard JSON serialization
            return json.dumps(value, default=str).encode(self.encoding)

    def loads(self, value: str) -> Any:
        if value is None:
            return None

        return json.loads(value)
