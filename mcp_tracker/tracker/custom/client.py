from typing import Any

from aiohttp import ClientSession, ClientTimeout
from pydantic import RootModel

from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User
from mcp_tracker.tracker.proto.users import UsersProtocol

QueueList = RootModel[list[Queue]]
LocalFieldList = RootModel[list[LocalField]]
QueueTagList = RootModel[list[str]]
VersionList = RootModel[list[QueueVersion]]
IssueLinkList = RootModel[list[IssueLink]]
IssueList = RootModel[list[Issue]]
IssueCommentList = RootModel[list[IssueComment]]
WorklogList = RootModel[list[Worklog]]
IssueAttachmentList = RootModel[list[IssueAttachment]]
GlobalFieldList = RootModel[list[GlobalField]]
StatusList = RootModel[list[Status]]
IssueTypeList = RootModel[list[IssueType]]
UserList = RootModel[list[User]]


class TrackerClient(QueuesProtocol, IssueProtocol, GlobalDataProtocol, UsersProtocol):
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

        if org_id:
            headers["X-Org-ID"] = org_id
        if cloud_org_id is not None:
            headers["X-Cloud-Org-ID"] = cloud_org_id
        if not org_id and not cloud_org_id:
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

    async def queues_get_local_fields(self, queue_id: str) -> list[LocalField]:
        async with self._session.get(f"v3/queues/{queue_id}/localFields") as response:
            response.raise_for_status()
            return LocalFieldList.model_validate_json(await response.read()).root

    async def queues_get_tags(self, queue_id: str) -> list[str]:
        async with self._session.get(f"v3/queues/{queue_id}/tags") as response:
            response.raise_for_status()
            return QueueTagList.model_validate_json(await response.read()).root

    async def queues_get_versions(self, queue_id: str) -> list[QueueVersion]:
        async with self._session.get(f"v3/queues/{queue_id}/versions") as response:
            response.raise_for_status()
            return VersionList.model_validate_json(await response.read()).root

    async def get_global_fields(self) -> list[GlobalField]:
        async with self._session.get("v3/fields") as response:
            response.raise_for_status()
            return GlobalFieldList.model_validate_json(await response.read()).root

    async def get_statuses(self) -> list[Status]:
        async with self._session.get("v3/statuses") as response:
            response.raise_for_status()
            return StatusList.model_validate_json(await response.read()).root

    async def get_issue_types(self) -> list[IssueType]:
        async with self._session.get("v3/issuetypes") as response:
            response.raise_for_status()
            return IssueTypeList.model_validate_json(await response.read()).root

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
        query: str,
        *,
        per_page: int = 15,
        page: int = 1,
    ) -> list[Issue]:
        params = {
            "perPage": per_page,
            "page": page,
        }

        body: dict[str, Any] = {
            "query": query,
        }

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

    async def issue_get_attachments(
        self, issue_id: str
    ) -> list[IssueAttachment] | None:
        async with self._session.get(f"v3/issues/{issue_id}/attachments") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return IssueAttachmentList.model_validate_json(await response.read()).root

    async def users_list(self, per_page: int = 50, page: int = 1) -> list[User]:
        params: dict[str, str | int] = {
            "perPage": per_page,
            "page": page,
        }
        async with self._session.get("v3/users", params=params) as response:
            response.raise_for_status()
            return UserList.model_validate_json(await response.read()).root

    async def user_get(self, user_id: str) -> User | None:
        async with self._session.get(f"v3/users/{user_id}") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return User.model_validate_json(await response.read())

    async def issues_count(self, query: str) -> int:
        body: dict[str, Any] = {
            "query": query,
        }

        async with self._session.post("v3/issues/_count", json=body) as response:
            response.raise_for_status()
            return int(await response.text())
