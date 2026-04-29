"""Protocol for Yandex Tracker Goal entity operations."""

from typing import Any, Protocol, runtime_checkable

from .common import YandexAuth
from .types.goals import Goal


@runtime_checkable
class GoalsProtocol(Protocol):
    async def goal_get(
        self,
        goal_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> Goal: ...

    async def goal_create(
        self,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Goal: ...

    async def goal_update(
        self,
        goal_id: str,
        *,
        fields: dict[str, Any],
        version: int | None = None,
        auth: YandexAuth | None = None,
    ) -> Goal: ...

    async def goal_delete(
        self,
        goal_id: str,
        *,
        auth: YandexAuth | None = None,
    ) -> None: ...

    async def goals_search(
        self,
        *,
        input: str | None = None,
        filter: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[Goal]: ...


class GoalsProtocolWrap(GoalsProtocol):
    def __init__(self, original: GoalsProtocol):
        self._original = original

    async def goal_get(
        self,
        goal_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> Goal:
        return await self._original.goal_get(goal_id, fields=fields, auth=auth)

    async def goal_create(
        self,
        *,
        fields: dict[str, Any],
        auth: YandexAuth | None = None,
    ) -> Goal:
        return await self._original.goal_create(fields=fields, auth=auth)

    async def goal_update(
        self,
        goal_id: str,
        *,
        fields: dict[str, Any],
        version: int | None = None,
        auth: YandexAuth | None = None,
    ) -> Goal:
        return await self._original.goal_update(
            goal_id, fields=fields, version=version, auth=auth
        )

    async def goal_delete(
        self,
        goal_id: str,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        return await self._original.goal_delete(goal_id, auth=auth)

    async def goals_search(
        self,
        *,
        input: str | None = None,
        filter: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[Goal]:
        return await self._original.goals_search(
            input=input,
            filter=filter,
            order_by=order_by,
            order_asc=order_asc,
            root_only=root_only,
            per_page=per_page,
            page=page,
            fields=fields,
            auth=auth,
        )
