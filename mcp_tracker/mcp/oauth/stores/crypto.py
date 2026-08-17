import base64

from cryptography.fernet import Fernet, MultiFernet


class FieldEncryptor:
    """Fernet encryption with key rotation support.

    First key is used for encryption; all keys are tried for decryption.
    """

    def __init__(self, keys: list[bytes]) -> None:
        if not keys:
            raise ValueError("At least one encryption key required")
        fernets = [Fernet(base64.urlsafe_b64encode(k)) for k in keys]
        self._multi_fernet = MultiFernet(fernets)

    def encrypt(self, value: str) -> str:
        """Encrypt a string value with the primary key."""
        return self._multi_fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        """Decrypt a string value with any available key."""
        return self._multi_fernet.decrypt(value.encode()).decode()
