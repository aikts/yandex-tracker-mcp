"""Issue and comment template MCP tools (read-only)."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.params import (
    CommentTemplateID,
    IssueTemplateID,
    PageOrAllParam,
    PerPageParam,
    QueueIDFilter,
)
from mcp_tracker.mcp.tools._access import check_queue_access, is_queue_allowed
from mcp_tracker.mcp.tools._pagination import collect_pages
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.pagination import PaginatedResult
from mcp_tracker.tracker.proto.types.templates import (
    BaseTemplate,
    CommentTemplate,
    IssueTemplate,
)

TemplateT = TypeVar("TemplateT", bound=BaseTemplate)


def _visible_templates(
    settings: Settings, templates: list[TemplateT]
) -> list[TemplateT]:
    """Drop templates bound to a queue outside ``TRACKER_LIMIT_QUEUES``.

    Templates without a queue are not queue-scoped (e.g. personal templates)
    and stay visible.
    """
    return [
        template
        for template in templates
        if template.queue is None
        or (
            template.queue.key is not None
            and is_queue_allowed(settings, template.queue.key)
        )
    ]


def _check_template_access(settings: Settings, template: BaseTemplate) -> None:
    """Reject a template belonging to a queue the server may not access."""
    if template.queue is not None and template.queue.key is not None:
        check_queue_access(settings, template.queue.key)


async def _collect_templates(
    settings: Settings,
    fetch: Callable[[int], Awaitable[PaginatedResult[TemplateT]]],
    page: int | None,
    per_page: int,
) -> PaginatedResult[TemplateT]:
    """Collect the visible templates of every page, or of ``page`` alone.

    Both template endpoints paginate with a default of 50 items per page, so a
    single request would silently drop everything past the first page.
    """
    return await collect_pages(
        fetch,
        page=page,
        per_page=per_page,
        visible=lambda templates: _visible_templates(settings, templates),
        restricted=bool(settings.tracker_limit_queues),
    )


def register_template_tools(settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register issue and comment template tools (all read-only)."""

    @mcp.tool(
        title="Get Issue Templates",
        description="Get the issue templates configured in Yandex Tracker. "
        "Templates hold the issue structure a team actually uses for bugs, incidents and other "
        "recurring work. Use this before creating an issue so that its summary and description "
        "follow the team's current template instead of an invented structure. "
        "Pass `queue` to get only the templates usable in that queue - the templates of that "
        "queue plus the ones not bound to any queue, which are usable everywhere. "
        "The issue body of each template is in `fieldTemplates.description`, not in the "
        "template's own `description`, which describes the template itself. "
        "Every page is retrieved by default; pass `page` to get a single page when the result "
        "does not fit the context window.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_templates_get_all(
        ctx: Context[Any, AppContext],
        queue: QueueIDFilter = None,
        page: PageOrAllParam = None,
        per_page: PerPageParam = 50,
    ) -> PaginatedResult[IssueTemplate]:
        if queue is not None:
            check_queue_access(settings, queue)

        return await _collect_templates(
            settings,
            lambda current_page: (
                ctx.request_context.lifespan_context.templates.get_issue_templates(
                    queue=queue,
                    per_page=per_page,
                    page=current_page,
                    auth=get_yandex_auth(ctx),
                )
            ),
            page,
            per_page,
        )

    @mcp.tool(
        title="Get Issue Template",
        description="Get a single Yandex Tracker issue template by its id, including the field "
        "values it prefills. Use `issue_templates_get_all` first to find the template id. "
        "The issue body lives in `fieldTemplates.description`; the template's own `description` "
        "describes the template itself and is usually empty.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def issue_template_get(
        ctx: Context[Any, AppContext],
        template_id: IssueTemplateID,
    ) -> IssueTemplate:
        template = (
            await ctx.request_context.lifespan_context.templates.get_issue_template(
                template_id,
                auth=get_yandex_auth(ctx),
            )
        )
        _check_template_access(settings, template)
        return template

    @mcp.tool(
        title="Get Comment Templates",
        description="Get the comment templates configured in Yandex Tracker. "
        "Templates hold the wording a team reuses when replying on issues, together with the "
        "users and mailing lists such a comment summons. Use this before adding a comment so it "
        "follows the team's current template instead of an invented one. "
        "Pass `queue` to get only the templates usable in that queue - the templates of that "
        "queue plus the ones not bound to any queue, which are usable everywhere. "
        "Every page is retrieved by default; pass `page` to get a single page when the result "
        "does not fit the context window.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def comment_templates_get_all(
        ctx: Context[Any, AppContext],
        queue: QueueIDFilter = None,
        page: PageOrAllParam = None,
        per_page: PerPageParam = 50,
    ) -> PaginatedResult[CommentTemplate]:
        if queue is not None:
            check_queue_access(settings, queue)

        return await _collect_templates(
            settings,
            lambda current_page: (
                ctx.request_context.lifespan_context.templates.get_comment_templates(
                    queue=queue,
                    per_page=per_page,
                    page=current_page,
                    auth=get_yandex_auth(ctx),
                )
            ),
            page,
            per_page,
        )

    @mcp.tool(
        title="Get Comment Template",
        description="Get a single Yandex Tracker comment template by its id, including the "
        "comment text it inserts. Use `comment_templates_get_all` first to find the template id.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def comment_template_get(
        ctx: Context[Any, AppContext],
        template_id: CommentTemplateID,
    ) -> CommentTemplate:
        template = (
            await ctx.request_context.lifespan_context.templates.get_comment_template(
                template_id,
                auth=get_yandex_auth(ctx),
            )
        )
        _check_template_access(settings, template)
        return template
