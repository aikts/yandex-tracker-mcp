from dataclasses import dataclass, field, fields

from mcp_tracker.crypto import hash_token

# Marks a field whose value must never be rendered verbatim.
SECRET = {"secret": True}

# Length (in hex chars) of the fingerprint standing in for a secret. 128 bits of
# SHA-256 keeps cache keys short while making a collision between two distinct
# tokens - and with it a cross-caller cache hit - practically impossible.
_FINGERPRINT_LENGTH = 32


def secret_fingerprint(secret: str | None) -> str:
    """Return a stable, non-reversible identifier for a secret."""
    if secret is None:
        return "none"
    return f"sha256:{hash_token(secret)[:_FINGERPRINT_LENGTH]}"


@dataclass
class YandexAuth:
    token: str | None = field(default=None, metadata=SECRET)
    cloud_org_id: str | None = None
    org_id: str | None = None

    def __repr__(self) -> str:
        """Render every field, secrets as a fingerprint.

        aiocache builds cache keys by stringifying the arguments of a cached
        method, so this repr ends up in the Redis key namespace (visible to
        KEYS/SCAN/MONITOR, RDB dumps and per-key metrics) as well as in logs and
        tracebacks. Fingerprinting the token keeps entries distinct per caller -
        no cross-caller cache hits - without writing the secret anywhere.
        """
        parts = []
        for f in fields(self):
            value = getattr(self, f.name)
            rendered = (
                secret_fingerprint(value) if f.metadata.get("secret") else repr(value)
            )
            parts.append(f"{f.name}={rendered}")
        return f"{type(self).__name__}({', '.join(parts)})"
