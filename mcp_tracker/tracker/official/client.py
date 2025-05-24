import asyncio
import datetime
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from typing import Callable, ParamSpec, TypeVar, Any

from yandex_tracker_client import TrackerClient
from yandex_tracker_client.exceptions import NotFound
from yandex_tracker_client.objects import Reference

from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueComment,
    IssueLink,
    LinkTypeReference,
)
from mcp_tracker.tracker.proto.types.refs import IssueTypeReference, PriorityReference, StatusReference, UserReference
from mcp_tracker.tracker.proto.types.queues import Queue

P = ParamSpec("P")
T = TypeVar("T")


class TrackerOfficialClient(IssueProtocol, QueuesProtocol):
    def __init__(
        self,
        *,
        token: str,
        org_id: str | None = None,
        base_url: str = "https://api.tracker.yandex.net",
        timeout: int = 10,
        cloud_org_id: str | None = None,
        iam_token: str | None = None,
        pool_workers: int | None = None,
    ):
        self._client = TrackerClient(
            token=token,
            org_id=org_id,
            cloud_org_id=cloud_org_id,
            base_url=base_url,
            timeout=timeout,
            iam_token=iam_token,
        )
        self._executor = ThreadPoolExecutor(max_workers=pool_workers)

    async def _run_in_executor(
        self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs
    ) -> T:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self._executor, partial(func, *args, **kwargs)
        )
        return result

    def _parse_user_reference(self, user_ref: Reference) -> UserReference:
        return UserReference(
            uid=user_ref.uid,
            login=user_ref.login,
            display=user_ref.display,
            email=user_ref.email,
            firstName=user_ref.firstName,
            lastName=user_ref.lastName,
        )

    def _parse_issue(self, issue: Any) -> Issue:
        return Issue(
            key=issue.key,
            summary=issue.summary,
            description=issue.display,
            type=IssueTypeReference(
                id=issue.type.id,
                display=issue.type.display,
                key=issue.type.key,
            ),
            priority=PriorityReference(
                id=issue.priority.id,
                key=issue.priority.key,
                display=issue.priority.display,
            ),
            status=StatusReference(
                key=issue.status.key,
                display=issue.status.display,
            ),
            components=[component.name for component in issue.components],
            # tags=issue.tags
            created_at=issue.createdAt,
            updated_at=issue.updatedAt,
            created_by=self._parse_user_reference(issue.createdBy),
            updated_by=self._parse_user_reference(issue.updatedBy),
            unique=issue.unique,
            start=issue.start,
            end=issue.start,
            deadline=issue.deadline,
        )

    def _parse_link(self, link: Any) -> IssueLink:
        return IssueLink(
            id=link.id,
            direction=link.direction,
            type=LinkTypeReference(
                id=link.type.id,
                inward=link.type.inward,
                outward=link.type.outward,
            ),
            object=self._parse_issue(link.object),
            created_at=link.createdAt,
            updated_at=link.updatedAt,
            created_by=self._parse_user_reference(link.createdBy),
            updated_by=self._parse_user_reference(link.updatedBy),
        )

    def _parse_queue(self, queue: Any) -> Queue:
        return Queue(
            id=queue.id,
            name=queue.name,
            description=queue.display,
            key=queue.key,
        )

    async def issue_get(self, issue_id: str) -> Issue | None:
        try:
            issue = await self._run_in_executor(self._client.issues.get, key=issue_id)
        except NotFound:
            return None

        return self._parse_issue(issue)

    async def issue_get_comments(self, issue_id: str) -> list[IssueComment] | None:
        try:
            issue = await self._run_in_executor(self._client.issues.get, key=issue_id)
        except NotFound:
            return None

        comments = []
        for comment in issue.comments:
            comments.append(
                IssueComment(
                    id=comment.id,
                    text=comment.text,
                    text_html=comment.textHtml,
                    created_at=comment.createdAt,
                    updated_at=comment.updatedAt,
                    created_by=self._parse_user_reference(comment.createdBy),
                    updated_by=self._parse_user_reference(comment.updatedBy),
                    summonees=[
                        self._parse_user_reference(ref) for ref in comment.summonees
                    ]
                    if comment.summonees
                    else None,
                )
            )

        return comments

    async def issues_find(
        self,
        queue: str,
        *,
        created_from: datetime.datetime | None = None,
        created_to: datetime.datetime | None = None,
        per_page: int = 15,
        page: int = 1,
    ) -> list[Issue]:
        filter_: dict[str, Any] = {
            "queue": queue,
        }

        if created_from is not None:
            filter_["created"] = {"from": created_from.isoformat()}

        if created_to is not None:
            if "created" not in filter_:
                filter_["created"] = {}

            filter_["created"] = {"to": created_to.isoformat()}

        issues_iter = await self._run_in_executor(
            self._client.issues.find,
            filter=filter_,
            per_page=per_page,
            page=page,
        )
        issues = issues_iter.get_page(page)

        return [self._parse_issue(iss) for iss in issues]

    async def issues_get_links(self, issue_id: str) -> list[IssueLink]:
        def _getter(issue_id: str):
            return self._client.issues[issue_id].links.get_all()

        links = await self._run_in_executor(_getter, issue_id)

        return [self._parse_link(link) for link in links]

    async def queues_list(self) -> list[Queue]:
        queues = await self._run_in_executor(self._client.queues.get_all)
        return [self._parse_queue(queue) for queue in queues]

    # async def create_issue(self, queue: str, issue: Issue) -> Issue:
    #     extra = {}
    #
    #     if issue.components:
    #         extra["components"] = [{"name": name} for name in issue.components]
    #
    #     if issue.tags:
    #         extra["tags"] = issue.tags
    #
    #     if issue.assignee is not None:
    #         extra["assignee"] = issue.assignee
    #
    #     if issue.priority is not None:
    #         extra["priority"] = issue.priority
    #
    #     if issue.description is not None:
    #         extra["description"] = issue.description
    #
    #     if issue.type is not None:
    #         extra["type"] = {"name": issue.type.name}
    #
    #     tracker_issue = self._client.issues.create(
    #         queue=queue,
    #         summary=issue.summary,
    #         **extra,
    #     )
