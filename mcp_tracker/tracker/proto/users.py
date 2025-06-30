from typing import Protocol

from .common import YandexAuth
from .types.users import User


class UsersProtocol(Protocol):
    async def users_list(
        self, per_page: int = 50, page: int = 1, *, auth: YandexAuth | None = None
    ) -> list[User]: ...

    async def user_get(
        self, user_id: str, *, auth: YandexAuth | None = None
    ) -> User | None: ...

    async def user_get_current(self, *, auth: YandexAuth | None = None) -> User: ...


class UsersProtocolWrap(UsersProtocol):
    def __init__(self, original: UsersProtocol):
        self._original = original
