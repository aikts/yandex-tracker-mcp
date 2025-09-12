import asyncio
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal

import jwt
import yandexcloud
from aiohttp import ClientSession, ClientTimeout
from pydantic import BaseModel, RootModel
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import IamTokenServiceStub

from mcp_tracker.tracker.custom.errors import IssueNotFound
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


logger = logging.getLogger(__name__)


class ServiceAccountSettings(BaseModel):
    key_id: str
    service_account_id: str
    private_key: str

    def to_yandexcloud_dict(self) -> dict[str, str]:
        return {
            "id": self.key_id,
            "service_account_id": self.service_account_id,
            "private_key": self.private_key,
        }


class IAMTokenInfo(BaseModel):
    token: str


class ServiceAccountStore:
    def __init__(self, settings: ServiceAccountSettings):
        self._settings = settings

        self._yc_sdk = yandexcloud.SDK(
            service_account_key=self._settings.to_yandexcloud_dict()
        )
        self._iam_service = self._yc_sdk.client(IamTokenServiceStub)
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._iam_token: IAMTokenInfo | None = None
        self._lock = asyncio.Lock()
        self._refresh_task: asyncio.Task[None] | None = None

    async def prepare(self):
        self._refresh_task = asyncio.create_task(self._refresher())

    async def close(self):
        try:
            if self._refresh_task is not None:
                self._refresh_task.cancel()
                await self._refresh_task
                self._refresh_task = None
        except Exception as e:
            logger.error("error while closing ServiceAccountStore: %s", e)

    async def get_iam_token(self, *, force_refresh: bool = False) -> str:
        if force_refresh or self._iam_token is None:
            async with self._lock:
                if not force_refresh and self._iam_token is not None:
                    return self._iam_token.token

                iam_token = await asyncio.get_running_loop().run_in_executor(
                    self._executor, self._fetch_iam_token, self._settings
                )

                self._iam_token = iam_token
                logger.info("Successfully fetched new IAM token.")

        return self._iam_token.token

    async def _refresher(self):
        while True:
            try:
                await self.get_iam_token(force_refresh=True)
                await asyncio.sleep(3500 + random.random() * 100)
            except asyncio.CancelledError:
                return

    def _fetch_iam_token(self, service_account: ServiceAccountSettings) -> IAMTokenInfo:
        now = int(time.time())
        payload = {
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            "iss": service_account.service_account_id,
            "iat": now,
            "exp": now + 3600,
        }

        jwt_token = jwt.encode(
            payload=payload,
            key=service_account.private_key,
            algorithm="PS256",
            headers={"kid": service_account.key_id},
        )

        iam_token = self._iam_service.Create(CreateIamTokenRequest(jwt=jwt_token))
        return IAMTokenInfo(token=iam_token.iam_token)


class TrackerClient(QueuesProtocol, IssueProtocol, GlobalDataProtocol, UsersProtocol):
    def __init__(
        self,
        *,
        token: str | None,
        iam_token: str | None = None,
        token_type: Literal["Bearer", "OAuth"] | None = None,
        service_account: ServiceAccountSettings | None = None,
        org_id: str | None = None,
        cloud_org_id: str | None = None,
        base_url: str = "https://api.tracker.yandex.net",
        timeout: float = 10,
    ):
        self._token = token
        self._token_type = token_type
        self._static_iam_token = iam_token
        self._service_account_store: ServiceAccountStore | None = (
            ServiceAccountStore(service_account) if service_account else None
        )
        self._org_id = org_id
        self._cloud_org_id = cloud_org_id

        self._session = ClientSession(
            base_url=base_url,
            timeout=ClientTimeout(total=timeout),
        )

    async def prepare(self):
        if self._service_account_store:
            await self._service_account_store.prepare()

    async def close(self):
        if self._service_account_store:
            await self._service_account_store.close()
        await self._session.close()

    async def _build_headers(self, auth: YandexAuth | None = None) -> dict[str, str]:
        # Priority: OAuth from auth > static OAuth > static IAM token > service account
        auth_header = None

        if auth and auth.token:
            token_type = self._token_type or "OAuth"
            auth_header = f"{token_type} {auth.token}"
        elif self._token:
            token_type = self._token_type or "OAuth"
            auth_header = f"{token_type} {self._token}"
        elif self._static_iam_token:
            auth_header = f"Bearer {self._static_iam_token}"
        elif self._service_account_store is not None:
            iam_token = await self._service_account_store.get_iam_token()
            auth_header = f"Bearer {iam_token}"

        if not auth_header:
            raise ValueError(
                "No authentication method provided. "
                "Provide either OAuth token, IAM token, or use OAuth flow."
            )

        headers = {"Authorization": auth_header}

        # Handle org_id logic
        org_id = auth.org_id if auth and auth.org_id else self._org_id
        cloud_org_id = (
            auth.cloud_org_id if auth and auth.cloud_org_id else self._cloud_org_id
        )

        if org_id and cloud_org_id:
            raise ValueError("Only one of org_id or cloud_org_id should be provided.")

        if org_id:
            headers["X-Org-ID"] = org_id
        elif cloud_org_id:
            headers["X-Cloud-Org-ID"] = cloud_org_id
        else:
            raise ValueError("Either org_id or cloud_org_id must be provided.")

        return headers

    async def queues_list(
        self, per_page: int = 100, page: int = 1, *, auth: YandexAuth | None = None
    ) -> list[Queue]:
        params = {
            "perPage": per_page,
            "page": page,
        }
        async with self._session.get(
            "v3/queues", headers=await self._build_headers(auth), params=params
        ) as response:
            response.raise_for_status()
            return QueueList.model_validate_json(await response.read()).root

    async def queues_get_local_fields(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[LocalField]:
        async with self._session.get(
            f"v3/queues/{queue_id}/localFields", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return LocalFieldList.model_validate_json(await response.read()).root

    async def queues_get_tags(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[str]:
        async with self._session.get(
            f"v3/queues/{queue_id}/tags", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return QueueTagList.model_validate_json(await response.read()).root

    async def queues_get_versions(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[QueueVersion]:
        async with self._session.get(
            f"v3/queues/{queue_id}/versions", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return VersionList.model_validate_json(await response.read()).root

    async def get_global_fields(
        self, *, auth: YandexAuth | None = None
    ) -> list[GlobalField]:
        async with self._session.get(
            "v3/fields", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return GlobalFieldList.model_validate_json(await response.read()).root

    async def get_statuses(self, *, auth: YandexAuth | None = None) -> list[Status]:
        async with self._session.get(
            "v3/statuses", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return StatusList.model_validate_json(await response.read()).root

    async def get_issue_types(
        self, *, auth: YandexAuth | None = None
    ) -> list[IssueType]:
        async with self._session.get(
            "v3/issuetypes", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return IssueTypeList.model_validate_json(await response.read()).root

    async def get_priorities(self, *, auth: YandexAuth | None = None) -> list[Priority]:
        async with self._session.get(
            "v3/priorities", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return PriorityList.model_validate_json(await response.read()).root

    async def issue_get(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> Issue:
        async with self._session.get(
            f"v3/issues/{issue_id}", headers=await self._build_headers(auth)
        ) as response:
            if response.status == 404:
                raise IssueNotFound(issue_id)
            response.raise_for_status()
            return Issue.model_validate_json(await response.read())

    async def issues_get_links(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueLink]:
        async with self._session.get(
            f"v3/issues/{issue_id}/links", headers=await self._build_headers(auth)
        ) as response:
            if response.status == 404:
                raise IssueNotFound(issue_id)
            response.raise_for_status()
            return IssueLinkList.model_validate_json(await response.read()).root

    async def issue_get_comments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueComment]:
        async with self._session.get(
            f"v3/issues/{issue_id}/comments", headers=await self._build_headers(auth)
        ) as response:
            if response.status == 404:
                raise IssueNotFound(issue_id)
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
            headers=await self._build_headers(auth),
            json=body,
            params=params,
        ) as response:
            response.raise_for_status()
            return IssueList.model_validate_json(await response.read()).root

    async def issue_get_worklogs(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Worklog]:
        async with self._session.get(
            f"v3/issues/{issue_id}/worklog", headers=await self._build_headers(auth)
        ) as response:
            if response.status == 404:
                raise IssueNotFound(issue_id)
            response.raise_for_status()
            return WorklogList.model_validate_json(await response.read()).root

    async def issue_get_attachments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueAttachment]:
        async with self._session.get(
            f"v3/issues/{issue_id}/attachments", headers=await self._build_headers(auth)
        ) as response:
            if response.status == 404:
                raise IssueNotFound(issue_id)
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
            "v3/users", headers=await self._build_headers(auth), params=params
        ) as response:
            response.raise_for_status()
            return UserList.model_validate_json(await response.read()).root

    async def user_get(
        self, user_id: str, *, auth: YandexAuth | None = None
    ) -> User | None:
        async with self._session.get(
            f"v3/users/{user_id}", headers=await self._build_headers(auth)
        ) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return User.model_validate_json(await response.read())

    async def user_get_current(self, *, auth: YandexAuth | None = None) -> User:
        async with self._session.get(
            "v3/myself", headers=await self._build_headers(auth)
        ) as response:
            response.raise_for_status()
            return User.model_validate_json(await response.read())

    async def issue_get_checklist(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[ChecklistItem]:
        async with self._session.get(
            f"v3/issues/{issue_id}/checklistItems",
            headers=await self._build_headers(auth),
        ) as response:
            if response.status == 404:
                raise IssueNotFound(issue_id)
            response.raise_for_status()
            return ChecklistItemList.model_validate_json(await response.read()).root

    async def issues_count(self, query: str, *, auth: YandexAuth | None = None) -> int:
        body: dict[str, Any] = {
            "query": query,
        }

        async with self._session.post(
            "v3/issues/_count", headers=await self._build_headers(auth), json=body
        ) as response:
            response.raise_for_status()
            return int(await response.text())
