import hashlib


def hash_token(token: str) -> str:
    """SHA-256 hash a token, for use where the raw token must not appear."""
    return hashlib.sha256(token.encode()).hexdigest()
