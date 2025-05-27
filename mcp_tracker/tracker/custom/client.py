import datetime
from typing import Any

from aiohttp import ClientSession, ClientTimeout
from pydantic import RootModel

from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.queues import Queue

QueueList = RootModel[list[Queue]]
IssueLinkList = RootModel[list[IssueLink]]
IssueList = RootModel[list[Issue]]
IssueCommentList = RootModel[list[IssueComment]]
WorklogList = RootModel[list[Worklog]]


class TrackerClient(QueuesProtocol, IssueProtocol):
    def __init__(
        self,
        *,
        token: str,
        org_id: str | None = None,
        base_url: str = "https://api.tracker.yandex.net",
        timeout: float = 10,
        cloud_org_id: str | None = None,
    ):
        headers = {
            "Authorization": f"OAuth {token}",
        }

        if org_id is not None:
            headers["X-Org-ID"] = org_id
        elif cloud_org_id is not None:
            headers["X-Cloud-Org-ID"] = cloud_org_id
        else:
            raise ValueError("Either org_id or cloud_org_id must be provided.")

        self._session = ClientSession(
            base_url=base_url,
            timeout=ClientTimeout(total=timeout),
            headers=headers,
        )

    async def close(self):
        await self._session.close()

    async def queues_list(self, per_page: int = 100, page: int = 1) -> list[Queue]:
        params = {
            "perPage": per_page,
            "page": page,
        }
        async with self._session.get("v3/queues", params=params) as response:
            response.raise_for_status()
            return QueueList.model_validate_json(await response.read()).root

    async def issue_get(self, issue_id: str) -> Issue | None:
        async with self._session.get(f"v3/issues/{issue_id}") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return Issue.model_validate_json(await response.read())

    async def issues_get_links(self, issue_id: str) -> list[IssueLink] | None:
        async with self._session.get(f"v3/issues/{issue_id}/links") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return IssueLinkList.model_validate_json(await response.read()).root

    async def issue_get_comments(self, issue_id: str) -> list[IssueComment] | None:
        async with self._session.get(f"v3/issues/{issue_id}/comments") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return IssueCommentList.model_validate_json(await response.read()).root

    async def issues_find(
        self,
        queue: str,
        *,
        created_from: datetime.datetime | None = None,
        created_to: datetime.datetime | None = None,
        per_page: int = 15,
        page: int = 1,
    ) -> list[Issue]:
        params = {
            "perPage": per_page,
            "page": page,
        }

        body: dict[str, Any] = {
            "filter": {
                "queue": queue,
            },
        }

        if created_from is not None:
            body["filter"]["created"] = {
                "from": created_from.isoformat(),
            }
            body["filter"]["created"]["from"] = created_from.isoformat()

        if created_to is not None:
            body["filter"].setdefault("created", {})
            body["filter"]["created"]["to"] = created_to.isoformat()

        async with self._session.post(
            "v3/issues/_search", json=body, params=params
        ) as response:
            response.raise_for_status()
            return IssueList.model_validate_json(await response.read()).root

    async def issue_get_worklogs(self, issue_id: str) -> list[Worklog] | None:
        async with self._session.get(f"v3/issues/{issue_id}/worklog") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return WorklogList.model_validate_json(await response.read()).root
