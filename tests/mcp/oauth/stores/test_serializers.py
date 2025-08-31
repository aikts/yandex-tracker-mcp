import json

import pytest
from pydantic import BaseModel

from mcp_tracker.mcp.oauth.stores.serializers import PydanticJsonSerializer


class SampleModel(BaseModel):
    name: str
    value: int


@pytest.fixture
def serializer() -> PydanticJsonSerializer:
    return PydanticJsonSerializer()


class TestPydanticJsonSerializerDumps:
    def test_dumps_pydantic_model(self, serializer: PydanticJsonSerializer) -> None:
        model = SampleModel(name="test", value=42)

        result = serializer.dumps(model)

        assert isinstance(result, bytes)
        assert json.loads(result) == {"name": "test", "value": 42}

    def test_dumps_dict(self, serializer: PydanticJsonSerializer) -> None:
        data = {"key": "value", "number": 123}

        result = serializer.dumps(data)

        assert isinstance(result, bytes)
        assert json.loads(result) == data

    def test_dumps_list(self, serializer: PydanticJsonSerializer) -> None:
        data = [1, 2, 3]

        result = serializer.dumps(data)

        assert isinstance(result, bytes)
        assert json.loads(result) == data

    def test_dumps_string(self, serializer: PydanticJsonSerializer) -> None:
        data = "simple string"

        result = serializer.dumps(data)

        assert isinstance(result, bytes)
        assert json.loads(result) == data

    def test_dumps_none(self, serializer: PydanticJsonSerializer) -> None:
        result = serializer.dumps(None)

        assert isinstance(result, bytes)
        assert json.loads(result) is None


class TestPydanticJsonSerializerLoads:
    def test_loads_json_object(self, serializer: PydanticJsonSerializer) -> None:
        data = '{"name": "test", "value": 42}'

        result = serializer.loads(data)

        assert result == {"name": "test", "value": 42}

    def test_loads_json_array(self, serializer: PydanticJsonSerializer) -> None:
        data = "[1, 2, 3]"

        result = serializer.loads(data)

        assert result == [1, 2, 3]

    def test_loads_json_string(self, serializer: PydanticJsonSerializer) -> None:
        data = '"hello"'

        result = serializer.loads(data)

        assert result == "hello"

    def test_loads_none(self, serializer: PydanticJsonSerializer) -> None:
        result = serializer.loads(None)  # type: ignore[arg-type]

        assert result is None


class TestPydanticJsonSerializerRoundtrip:
    def test_roundtrip_pydantic_model(self, serializer: PydanticJsonSerializer) -> None:
        model = SampleModel(name="roundtrip", value=99)

        serialized = serializer.dumps(model)
        deserialized = serializer.loads(serialized.decode("utf-8"))

        assert deserialized == {"name": "roundtrip", "value": 99}

    def test_roundtrip_dict(self, serializer: PydanticJsonSerializer) -> None:
        data = {"nested": {"key": "value"}, "list": [1, 2, 3]}

        serialized = serializer.dumps(data)
        deserialized = serializer.loads(serialized.decode("utf-8"))

        assert deserialized == data
