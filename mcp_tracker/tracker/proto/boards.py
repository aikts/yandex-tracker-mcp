from typing import Protocol, runtime_checkable

from .common import YandexAuth
from .types.boards import Board, Sprint


@runtime_checkable
class BoardsProtocol(Protocol):
    async def boards_list(self, *, auth: YandexAuth | None = None) -> list[Board]: ...

    async def board_get_sprints(
        self, board_id: int, *, auth: YandexAuth | None = None
    ) -> list[Sprint]: ...


class BoardsProtocolWrap(BoardsProtocol):
    def __init__(self, original: BoardsProtocol):
        self._original = original
