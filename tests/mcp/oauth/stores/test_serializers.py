import json
import secrets

import pytest
from pydantic import BaseModel

from mcp_tracker.mcp.oauth.stores.crypto import FieldEncryptor
from mcp_tracker.mcp.oauth.stores.serializers import (
    EncryptedFieldSerializer,
    PydanticJsonSerializer,
)


class SampleModel(BaseModel):
    name: str
    value: int


class TokenModel(BaseModel):
    token: str
    client_id: str
    scopes: list[str]


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


class TestEncryptedFieldSerializerWithoutEncryption:
    """Tests for EncryptedFieldSerializer in passthrough mode (no encryption)."""

    @pytest.fixture
    def serializer(self) -> EncryptedFieldSerializer:
        return EncryptedFieldSerializer(encryptor=None)

    def test_dumps_pydantic_model_with_token(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        model = TokenModel(
            token="secret-token", client_id="client-123", scopes=["read", "write"]
        )

        result = serializer.dumps(model)
        data = json.loads(result)

        # Without encryption, token should be plaintext
        assert data["token"] == "secret-token"
        assert data["client_id"] == "client-123"
        assert data["scopes"] == ["read", "write"]

    def test_roundtrip_preserves_data(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        model = TokenModel(token="my-token", client_id="client", scopes=["scope1"])

        serialized = serializer.dumps(model)
        deserialized = serializer.loads(serialized.decode("utf-8"))

        assert deserialized["token"] == "my-token"
        assert deserialized["client_id"] == "client"


class TestEncryptedFieldSerializerWithEncryption:
    """Tests for EncryptedFieldSerializer with encryption enabled."""

    @pytest.fixture
    def encryptor(self) -> FieldEncryptor:
        key = secrets.token_bytes(32)
        return FieldEncryptor([key])

    @pytest.fixture
    def serializer(self, encryptor: FieldEncryptor) -> EncryptedFieldSerializer:
        return EncryptedFieldSerializer(encryptor=encryptor)

    def test_dumps_encrypts_token_field(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        model = TokenModel(
            token="secret-token", client_id="client-123", scopes=["read"]
        )

        result = serializer.dumps(model)
        data = json.loads(result)

        # Token should be encrypted (not equal to plaintext)
        assert data["token"] != "secret-token"
        # Non-sensitive fields should remain plaintext
        assert data["client_id"] == "client-123"
        assert data["scopes"] == ["read"]

    def test_dumps_encrypts_client_secret_field(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        data = {"client_id": "my-client", "client_secret": "super-secret"}

        result = serializer.dumps(data)
        loaded = json.loads(result)

        # client_secret should be encrypted
        assert loaded["client_secret"] != "super-secret"
        # client_id should remain plaintext
        assert loaded["client_id"] == "my-client"

    def test_loads_decrypts_token_field(
        self, serializer: EncryptedFieldSerializer, encryptor: FieldEncryptor
    ) -> None:
        # Create encrypted data
        encrypted_token = encryptor.encrypt("decrypted-token")
        encrypted_data = json.dumps(
            {"token": encrypted_token, "client_id": "client", "scopes": []}
        )

        result = serializer.loads(encrypted_data)

        assert result["token"] == "decrypted-token"
        assert result["client_id"] == "client"

    def test_roundtrip_with_encryption(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        model = TokenModel(
            token="roundtrip-token", client_id="client-456", scopes=["a", "b"]
        )

        serialized = serializer.dumps(model)
        # Verify encrypted form doesn't contain plaintext token
        assert b"roundtrip-token" not in serialized

        deserialized = serializer.loads(serialized.decode("utf-8"))

        assert deserialized["token"] == "roundtrip-token"
        assert deserialized["client_id"] == "client-456"
        assert deserialized["scopes"] == ["a", "b"]

    def test_handles_none_token_value(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        data = {"token": None, "client_id": "client"}

        serialized = serializer.dumps(data)
        deserialized = serializer.loads(serialized.decode("utf-8"))

        assert deserialized["token"] is None
        assert deserialized["client_id"] == "client"

    def test_handles_non_dict_values(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        # Non-dict values should pass through unchanged
        data = "plain string"

        serialized = serializer.dumps(data)
        deserialized = serializer.loads(serialized.decode("utf-8"))

        assert deserialized == "plain string"

    def test_loads_none_returns_none(
        self, serializer: EncryptedFieldSerializer
    ) -> None:
        result = serializer.loads(None)  # type: ignore[arg-type]

        assert result is None
