from typing import Any

from aiohttp import ClientSession, ClientTimeout
from pydantic import RootModel

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
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
ChecklistItemList = RootModel[list[ChecklistItem]]
GlobalFieldList = RootModel[list[GlobalField]]
StatusList = RootModel[list[Status]]
IssueTypeList = RootModel[list[IssueType]]
PriorityList = RootModel[list[Priority]]
UserList = RootModel[list[User]]


class TrackerClient(QueuesProtocol, IssueProtocol, GlobalDataProtocol, UsersProtocol):
    def __init__(
        self,
        *,
        token: str | None,
        org_id: str | None = None,
        base_url: str = "https://api.tracker.yandex.net",
        timeout: float = 10,
        cloud_org_id: str | None = None,
    ):
        self._token = token
        self._org_id = org_id
        self._cloud_org_id = cloud_org_id

        self._session = ClientSession(
            base_url=base_url,
            timeout=ClientTimeout(total=timeout),
        )

    async def close(self):
        await self._session.close()

    def _build_headers(self, auth: YandexAuth | None = None) -> dict[str, str]:
        if auth is None:
            token = self._token
            org_id = self._org_id
            cloud_org_id = self._cloud_org_id
        else:
            token = auth.token or self._token
            org_id = auth.org_id or self._org_id
            cloud_org_id = auth.cloud_org_id or self._cloud_org_id

        assert token is not None, (
            "Token must be provided - either statically or by OAuth"
        )

        headers = {
            "Authorization": f"OAuth {token}",
        }

        if org_id and cloud_org_id:
            raise ValueError("Only one of org_id or cloud_org_id should be provided.")

        if not org_id and not cloud_org_id:
            raise ValueError("Either org_id or cloud_org_id must be provided.")

        if org_id:
            headers["X-Org-ID"] = org_id

        if cloud_org_id is not None:
            headers["X-Cloud-Org-ID"] = cloud_org_id

        return headers

    async def queues_list(
        self, per_page: int = 100, page: int = 1, *, auth: YandexAuth | None = None
    ) -> list[Queue]:
        params = {
            "perPage": per_page,
            "page": page,
        }
        async with self._session.get(
            "v3/queues", headers=self._build_headers(auth), params=params
        ) as response:
            response.raise_for_status()
            return QueueList.model_validate_json(await response.read()).root

    async def queues_get_local_fields(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[LocalField]:
        async with self._session.get(
            f"v3/queues/{queue_id}/localFields", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return LocalFieldList.model_validate_json(await response.read()).root

    async def queues_get_tags(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[str]:
        async with self._session.get(
            f"v3/queues/{queue_id}/tags", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return QueueTagList.model_validate_json(await response.read()).root

    async def queues_get_versions(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[QueueVersion]:
        async with self._session.get(
            f"v3/queues/{queue_id}/versions", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return VersionList.model_validate_json(await response.read()).root

    async def get_global_fields(
        self, *, auth: YandexAuth | None = None
    ) -> list[GlobalField]:
        async with self._session.get(
            "v3/fields", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return GlobalFieldList.model_validate_json(await response.read()).root

    async def get_statuses(self, *, auth: YandexAuth | None = None) -> list[Status]:
        async with self._session.get(
            "v3/statuses", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return StatusList.model_validate_json(await response.read()).root

    async def get_issue_types(
        self, *, auth: YandexAuth | None = None
    ) -> list[IssueType]:
        async with self._session.get(
            "v3/issuetypes", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return IssueTypeList.model_validate_json(await response.read()).root

    async def get_priorities(self, *, auth: YandexAuth | None = None) -> list[Priority]:
        async with self._session.get(
            "v3/priorities", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return PriorityList.model_validate_json(await response.read()).root

    async def issue_get(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> Issue | None:
        async with self._session.get(
            f"v3/issues/{issue_id}", headers=self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return Issue.model_validate_json(await response.read())

    async def issues_get_links(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueLink] | None:
        async with self._session.get(
            f"v3/issues/{issue_id}/links", headers=self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return IssueLinkList.model_validate_json(await response.read()).root

    async def issue_get_comments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueComment] | None:
        async with self._session.get(
            f"v3/issues/{issue_id}/comments", headers=self._build_headers(auth)
        ) as response:
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
        auth: YandexAuth | None = None,
    ) -> list[Issue]:
        params = {
            "perPage": per_page,
            "page": page,
        }

        body: dict[str, Any] = {
            "query": query,
        }

        async with self._session.post(
            "v3/issues/_search",
            headers=self._build_headers(auth),
            json=body,
            params=params,
        ) as response:
            response.raise_for_status()
            return IssueList.model_validate_json(await response.read()).root

    async def issue_get_worklogs(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Worklog] | None:
        async with self._session.get(
            f"v3/issues/{issue_id}/worklog", headers=self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return WorklogList.model_validate_json(await response.read()).root

    async def issue_get_attachments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueAttachment] | None:
        async with self._session.get(
            f"v3/issues/{issue_id}/attachments", headers=self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return IssueAttachmentList.model_validate_json(await response.read()).root

    async def users_list(
        self, per_page: int = 50, page: int = 1, *, auth: YandexAuth | None = None
    ) -> list[User]:
        params: dict[str, str | int] = {
            "perPage": per_page,
            "page": page,
        }
        async with self._session.get(
            "v3/users", headers=self._build_headers(auth), params=params
        ) as response:
            response.raise_for_status()
            return UserList.model_validate_json(await response.read()).root

    async def user_get(
        self, user_id: str, *, auth: YandexAuth | None = None
    ) -> User | None:
        async with self._session.get(
            f"v3/users/{user_id}", headers=self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return User.model_validate_json(await response.read())

    async def user_get_current(self, *, auth: YandexAuth | None = None) -> User:
        async with self._session.get(
            "v3/myself", headers=self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return User.model_validate_json(await response.read())

    async def issue_get_checklist(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[ChecklistItem] | None:
        async with self._session.get(
            f"v3/issues/{issue_id}/checklistItems", headers=self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return ChecklistItemList.model_validate_json(await response.read()).root

    async def issues_count(self, query: str, *, auth: YandexAuth | None = None) -> int:
        body: dict[str, Any] = {
            "query": query,
        }

        async with self._session.post(
            "v3/issues/_count", headers=self._build_headers(auth), json=body
        ) as response:
            response.raise_for_status()
            return int(await response.text())
