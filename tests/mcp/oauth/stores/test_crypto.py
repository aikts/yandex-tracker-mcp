import secrets

import pytest
from cryptography.fernet import InvalidToken

from mcp_tracker.mcp.oauth.stores.crypto import FieldEncryptor


class TestFieldEncryptorInit:
    def test_init_with_single_key(self) -> None:
        key = secrets.token_bytes(32)

        encryptor = FieldEncryptor([key])

        assert encryptor is not None

    def test_init_with_multiple_keys(self) -> None:
        keys = [secrets.token_bytes(32) for _ in range(3)]

        encryptor = FieldEncryptor(keys)

        assert encryptor is not None

    def test_init_with_empty_list_raises_error(self) -> None:
        with pytest.raises(ValueError, match="At least one encryption key required"):
            FieldEncryptor([])


class TestFieldEncryptorEncryptDecrypt:
    @pytest.fixture
    def encryptor(self) -> FieldEncryptor:
        key = secrets.token_bytes(32)
        return FieldEncryptor([key])

    def test_encrypt_returns_string(self, encryptor: FieldEncryptor) -> None:
        result = encryptor.encrypt("plaintext")

        assert isinstance(result, str)

    def test_encrypt_produces_different_output_than_input(
        self, encryptor: FieldEncryptor
    ) -> None:
        plaintext = "sensitive-data"

        ciphertext = encryptor.encrypt(plaintext)

        assert ciphertext != plaintext

    def test_decrypt_reverses_encryption(self, encryptor: FieldEncryptor) -> None:
        plaintext = "my secret token"

        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_roundtrip_preserves_unicode(self, encryptor: FieldEncryptor) -> None:
        plaintext = "тестовый токен 🔐"

        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_roundtrip_preserves_empty_string(self, encryptor: FieldEncryptor) -> None:
        plaintext = ""

        ciphertext = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(ciphertext)

        assert decrypted == plaintext

    def test_decrypt_with_wrong_key_raises_error(self) -> None:
        key1 = secrets.token_bytes(32)
        key2 = secrets.token_bytes(32)
        encryptor1 = FieldEncryptor([key1])
        encryptor2 = FieldEncryptor([key2])

        ciphertext = encryptor1.encrypt("secret")

        with pytest.raises(InvalidToken):
            encryptor2.decrypt(ciphertext)

    def test_decrypt_invalid_token_raises_error(
        self, encryptor: FieldEncryptor
    ) -> None:
        with pytest.raises(InvalidToken):
            encryptor.decrypt("not-a-valid-fernet-token")


class TestFieldEncryptorKeyRotation:
    def test_decrypt_with_old_key_after_rotation(self) -> None:
        old_key = secrets.token_bytes(32)
        new_key = secrets.token_bytes(32)

        # Encrypt with old key
        old_encryptor = FieldEncryptor([old_key])
        ciphertext = old_encryptor.encrypt("secret-data")

        # Create encryptor with new key first (for encryption), old key second (for decryption)
        rotated_encryptor = FieldEncryptor([new_key, old_key])

        # Should be able to decrypt old data
        decrypted = rotated_encryptor.decrypt(ciphertext)

        assert decrypted == "secret-data"

    def test_encrypt_with_new_key_after_rotation(self) -> None:
        old_key = secrets.token_bytes(32)
        new_key = secrets.token_bytes(32)

        # Create encryptor with both keys (new first)
        rotated_encryptor = FieldEncryptor([new_key, old_key])
        ciphertext = rotated_encryptor.encrypt("new-data")

        # New key-only encryptor should be able to decrypt
        new_only_encryptor = FieldEncryptor([new_key])
        decrypted = new_only_encryptor.decrypt(ciphertext)

        assert decrypted == "new-data"

        # Old key-only encryptor should NOT be able to decrypt
        old_only_encryptor = FieldEncryptor([old_key])
        with pytest.raises(InvalidToken):
            old_only_encryptor.decrypt(ciphertext)

    def test_multiple_key_rotation(self) -> None:
        keys = [secrets.token_bytes(32) for _ in range(5)]

        # Encrypt with oldest key
        oldest_encryptor = FieldEncryptor([keys[4]])
        ciphertext = oldest_encryptor.encrypt("data")

        # Encryptor with all keys should decrypt
        all_keys_encryptor = FieldEncryptor(keys)
        decrypted = all_keys_encryptor.decrypt(ciphertext)

        assert decrypted == "data"
