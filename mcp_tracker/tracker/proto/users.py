from typing import Protocol

from .types.users import User


class UsersProtocol(Protocol):
    async def users_list(
        self, per_page: int = 50, page: int = 1, *, token: str | None = None
    ) -> list[User]: ...

    async def user_get(
        self, user_id: str, *, token: str | None = None
    ) -> User | None: ...


class UsersProtocolWrap(UsersProtocol):
    def __init__(self, original: UsersProtocol):
        self._original = original
