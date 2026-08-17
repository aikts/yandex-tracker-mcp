from typing import Protocol, runtime_checkable

from .common import YandexAuth
from .types.templates import CommentTemplate, IssueTemplate


@runtime_checkable
class TemplatesProtocol(Protocol):
    async def get_issue_templates(
        self,
        *,
        queue: str | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[IssueTemplate]: ...
    async def get_issue_template(
        self, template_id: str, *, auth: YandexAuth | None = None
    ) -> IssueTemplate: ...
    async def get_comment_templates(
        self,
        *,
        queue: str | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> list[CommentTemplate]: ...
    async def get_comment_template(
        self, template_id: str, *, auth: YandexAuth | None = None
    ) -> CommentTemplate: ...


class TemplatesProtocolWrap(TemplatesProtocol):
    def __init__(self, original: TemplatesProtocol):
        self._original = original
