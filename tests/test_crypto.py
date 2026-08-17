from mcp_tracker.crypto import hash_token


class TestHashToken:
    def test_hash_token_returns_hex_string(self) -> None:
        result = hash_token("test-token")

        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex characters

    def test_hash_token_is_deterministic(self) -> None:
        token = "my-secret-token"

        result1 = hash_token(token)
        result2 = hash_token(token)

        assert result1 == result2

    def test_hash_token_different_inputs_produce_different_hashes(self) -> None:
        hash1 = hash_token("token-1")
        hash2 = hash_token("token-2")

        assert hash1 != hash2

    def test_hash_token_known_value(self) -> None:
        # Known SHA-256 hash of "test"
        expected = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        result = hash_token("test")

        assert result == expected
