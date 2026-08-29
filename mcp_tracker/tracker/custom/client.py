import asyncio
import datetime
import logging
import random
import time
from asyncio import CancelledError
from collections.abc import AsyncIterator, Collection, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any, Literal

import jwt
import yandexcloud
from aiohttp import ClientResponse, ClientSession, ClientTimeout
from pydantic import BaseModel, Field, RootModel
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import IamTokenServiceStub
from yarl import URL

from mcp_tracker.tracker.custom.errors import (
    BoardNotFound,
    ChecklistBatchPartiallyAdded,
    ChecklistItemEmptyUpdate,
    ChecklistItemNotFound,
    CommentTemplateNotFound,
    EntityLinksOnlyUpdate,
    IssueNotFound,
    IssueTemplateNotFound,
    IssueVersionConflict,
    QueueNotFound,
    TrackerAPIError,
    TrackerAPITimeout,
    YandexTrackerError,
)
from mcp_tracker.tracker.proto.boards import BoardsProtocol
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.entities import EntitiesProtocol
from mcp_tracker.tracker.proto.fields import GlobalDataProtocol
from mcp_tracker.tracker.proto.issues import IssueProtocol
from mcp_tracker.tracker.proto.queues import QueuesProtocol
from mcp_tracker.tracker.proto.templates import TemplatesProtocol
from mcp_tracker.tracker.proto.types.boards import Board, BoardColumnDetail, Sprint
from mcp_tracker.tracker.proto.types.entities import (
    DEFAULT_ENTITY_FIELDS_PARAM,
    GoalEntity,
    GoalSearchResult,
    GoalStatus,
    PortfolioEntity,
    PortfolioSearchResult,
    ProjectEntity,
    ProjectPortfolioStatus,
    ProjectSearchResult,
)
from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.inputs import (
    ChecklistItemDeadlineInput,
    ChecklistItemInput,
    EntityChecklistItemUpdateInput,
    EntityParentEntityInput,
    GoalLinkInput,
    IssueComponentRef,
    IssueFollowerRef,
    IssueParentRef,
    IssuePriorityRef,
    IssueProjectRef,
    IssueSprintRef,
    IssueTypeRef,
    ProjectPortfolioLinkInput,
)
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChangelogEntry,
    ChangelogPage,
    ChecklistItem,
    CommentsPage,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueLinkRelationship,
    IssueTransition,
    Worklog,
)
from mcp_tracker.tracker.proto.types.pagination import ItemT, PaginatedResult
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import (
    Queue,
    QueueExpandOption,
    QueueVersion,
)
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.templates import CommentTemplate, IssueTemplate
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


class EntityCommentsRelativePage(BaseModel):
    """Raw response of `GET /v3/entities/<type>/<id>/comments/_relative`.

    Unlike the issue comment endpoint, entity comments paginate through a
    dedicated `_relative` endpoint that answers with an object and signals more
    pages via `hasNext` rather than a `Link` header.
    """

    comments: list[IssueComment] = Field(default_factory=list)
    hasNext: bool = False
    hasPrev: bool = False


class _ChecklistSnapshotFields(BaseModel):
    checklistItems: list[ChecklistItem] = Field(default_factory=list)


class _ChecklistSnapshot(BaseModel):
    """Minimal parse of a `GET /v3/entities/<type>/<id>?fields=checklistItems`
    response, used to reconcile a partial `*_update_checklist` call - see
    `TrackerClient._reconcile_checklist_update`.
    """

    fields: _ChecklistSnapshotFields = Field(default_factory=_ChecklistSnapshotFields)


class _IssueChecklist(_ChecklistSnapshotFields):
    """Minimal parse of the issue payload the issue checklist write endpoints
    answer with - only the resulting checklist is of interest to the caller.

    The key is absent once the last item is deleted, hence the default.
    """


GlobalFieldList = RootModel[list[GlobalField]]
StatusList = RootModel[list[Status]]
IssueTypeList = RootModel[list[IssueType]]
PriorityList = RootModel[list[Priority]]
ResolutionList = RootModel[list[Resolution]]
IssueTemplateList = RootModel[list[IssueTemplate]]
CommentTemplateList = RootModel[list[CommentTemplate]]
UserList = RootModel[list[User]]
IssueTransitionList = RootModel[list[IssueTransition]]
ChangelogList = RootModel[list[ChangelogEntry]]
BoardList = RootModel[list[Board]]
BoardColumnList = RootModel[list[BoardColumnDetail]]
SprintList = RootModel[list[Sprint]]


logger = logging.getLogger(__name__)


def _ref_body(value: BaseModel | str | int) -> Any:
    """Serialize a reference field value for an issue create/update body.

    Reference models are sent as `{"id": ...}` / `{"key": ...}` objects, which
    Tracker resolves by identifier; bare scalars are passed through untouched
    and are resolved by Tracker as a key/login (string) or id (number).
    """
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True)
    return value


def _tracker_datetime(value: datetime.datetime) -> str:
    """Format a datetime the way Tracker wants it: `YYYY-MM-DDThh:mm:ss.ffffff+0000`.

    A naive datetime is read as UTC, and the offset is emitted without a colon -
    the form the API accepts.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z")


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
    DEFAULT_REFRESH_INTERVAL: float = 3500.0
    DEFAULT_RETRY_INTERVAL: float = 10.0

    def __init__(
        self,
        settings: ServiceAccountSettings,
        *,
        refresh_interval: float | None = None,
        retry_interval: float | None = None,
    ):
        self._settings = settings
        self._refresh_interval = refresh_interval or self.DEFAULT_REFRESH_INTERVAL
        self._retry_interval = retry_interval or self.DEFAULT_RETRY_INTERVAL

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
        except CancelledError:
            return
        except Exception as e:  # pragma: no cover
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
                interval = self._refresh_interval
            except asyncio.CancelledError:  # pragma: no cover
                return
            except Exception as e:
                logger.error("Error refreshing IAM token: %s", e)
                interval = self._retry_interval

            jitter = random.random() * min(interval * 0.1, 100)
            await asyncio.sleep(interval + jitter)

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


# `GET /v3/boards/_paginate` documents `perPage` as no more than 500.
BOARDS_PAGE_MAX = 500


class TrackerClient(
    QueuesProtocol,
    IssueProtocol,
    GlobalDataProtocol,
    TemplatesProtocol,
    UsersProtocol,
    EntitiesProtocol,
    BoardsProtocol,
):
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

        self._timeout = timeout
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

    @staticmethod
    async def _raise_for_status(response: ClientResponse) -> None:
        """Raise `TrackerAPIError` carrying the API's own explanation of the failure.

        `ClientResponse.raise_for_status()` discards the response body, which is
        where Tracker says *what* it did not like (e.g. which field of an
        issue_create call was rejected with 422), leaving the caller with a bare
        "Unprocessable Entity".
        """
        if response.status < 400:
            return

        try:
            body = await response.text()
        except Exception:  # pragma: no cover - body already consumed/aborted
            body = ""

        raise TrackerAPIError(
            status=response.status,
            method=response.method,
            url=str(response.url),
            body=body,
        )

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        url: str,
        *,
        auth: YandexAuth | None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        not_found: YandexTrackerError | None = None,
        conflict: YandexTrackerError | None = None,
        allow_statuses: Collection[int] = (),
    ) -> AsyncIterator[ClientResponse]:
        """Every request to the Tracker API goes through here.

        What is handled once here used to be repeated at each of the sixty call
        sites, which is one forgotten line away from a method that reports a
        failure worse than the rest: the timeout below reached the caller from a
        single method until this existed, and a missing `not_found` turns "no
        such issue" back into a bare 404.

        `allow_statuses` hands a status back to the caller instead of raising -
        for the one method that answers a 404 with `None` rather than an error.
        """
        # Built before the `try`: the service account's IAM fetch is not a
        # Tracker request and must not be reported as one timing out.
        headers = await self._build_headers(auth)

        try:
            async with self._session.request(
                method, url, headers=headers, params=params, json=json
            ) as response:
                if response.status not in allow_statuses:
                    if not_found is not None and response.status == 404:
                        raise not_found
                    if conflict is not None and response.status == 409:
                        raise conflict
                    await self._raise_for_status(response)
                yield response
        except TimeoutError as exc:
            # A body read that times out lands here too: it runs inside the
            # caller's `async with`, and that exception is thrown back in at the
            # `yield` above.
            raise TrackerAPITimeout(
                method=method, url=url, timeout=self._timeout
            ) from exc

    async def _read(
        self,
        method: str,
        url: str,
        *,
        auth: YandexAuth | None,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        not_found: YandexTrackerError | None = None,
        conflict: YandexTrackerError | None = None,
    ) -> bytes:
        """The body of a request whose caller needs nothing else from the response."""
        async with self._request(
            method,
            url,
            auth=auth,
            params=params,
            json=json,
            not_found=not_found,
            conflict=conflict,
        ) as response:
            return await response.read()

    async def queues_list(
        self, per_page: int = 100, page: int = 1, *, auth: YandexAuth | None = None
    ) -> PaginatedResult[Queue]:
        params = {
            "perPage": per_page,
            "page": page,
        }
        async with self._request(
            "GET", "v3/queues", auth=auth, params=params
        ) as response:
            return self._paginated(
                response, QueueList.model_validate_json(await response.read()).root
            )

    async def queues_get_local_fields(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[LocalField]:
        return LocalFieldList.model_validate_json(
            await self._read(
                "GET",
                f"v3/queues/{queue_id}/localFields",
                auth=auth,
                not_found=QueueNotFound(queue_id),
            )
        ).root

    async def queues_get_tags(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[str]:
        return QueueTagList.model_validate_json(
            await self._read(
                "GET",
                f"v3/queues/{queue_id}/tags",
                auth=auth,
                not_found=QueueNotFound(queue_id),
            )
        ).root

    async def queues_get_versions(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[QueueVersion]:
        return VersionList.model_validate_json(
            await self._read(
                "GET",
                f"v3/queues/{queue_id}/versions",
                auth=auth,
                not_found=QueueNotFound(queue_id),
            )
        ).root

    async def queue_create_version(
        self,
        queue_id: str,
        *,
        name: str,
        description: str | None = None,
        start_date: datetime.date | None = None,
        due_date: datetime.date | None = None,
        auth: YandexAuth | None = None,
    ) -> QueueVersion:
        body: dict[str, Any] = {"queue": queue_id, "name": name}
        if description is not None:
            body["description"] = description
        if start_date is not None:
            body["startDate"] = start_date.isoformat()
        if due_date is not None:
            body["dueDate"] = due_date.isoformat()

        return QueueVersion.model_validate_json(
            await self._read("POST", "v3/versions/", auth=auth, json=body)
        )

    async def queues_get_fields(
        self, queue_id: str, *, auth: YandexAuth | None = None
    ) -> list[GlobalField]:
        return GlobalFieldList.model_validate_json(
            await self._read(
                "GET",
                f"v3/queues/{queue_id}/fields",
                auth=auth,
                not_found=QueueNotFound(queue_id),
            )
        ).root

    async def queue_get(
        self,
        queue_id: str,
        *,
        expand: list[QueueExpandOption] | None = None,
        auth: YandexAuth | None = None,
    ) -> Queue:
        params: dict[str, str] = {}
        if expand:
            params["expand"] = ",".join(expand)

        return Queue.model_validate_json(
            await self._read(
                "GET",
                f"v3/queues/{queue_id}",
                auth=auth,
                params=params,
                not_found=QueueNotFound(queue_id),
            )
        )

    async def get_global_fields(
        self, *, auth: YandexAuth | None = None
    ) -> list[GlobalField]:
        return GlobalFieldList.model_validate_json(
            await self._read("GET", "v3/fields", auth=auth)
        ).root

    async def get_statuses(self, *, auth: YandexAuth | None = None) -> list[Status]:
        return StatusList.model_validate_json(
            await self._read("GET", "v3/statuses", auth=auth)
        ).root

    async def get_issue_types(
        self, *, auth: YandexAuth | None = None
    ) -> list[IssueType]:
        return IssueTypeList.model_validate_json(
            await self._read("GET", "v3/issuetypes", auth=auth)
        ).root

    async def get_priorities(self, *, auth: YandexAuth | None = None) -> list[Priority]:
        return PriorityList.model_validate_json(
            await self._read("GET", "v3/priorities", auth=auth)
        ).root

    async def get_resolutions(
        self, *, auth: YandexAuth | None = None
    ) -> list[Resolution]:
        return ResolutionList.model_validate_json(
            await self._read("GET", "v3/resolutions", auth=auth)
        ).root

    async def get_issue_templates(
        self,
        *,
        queue: str | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> PaginatedResult[IssueTemplate]:
        # The queue-scoped endpoint returns the templates of that queue plus the
        # ones not bound to any queue, which are usable in every queue.
        path = (
            "v3/issueTemplates"
            if queue is None
            else f"v3/queues/{queue}/issueTemplates"
        )
        params = {
            "perPage": per_page,
            "page": page,
        }
        async with self._request(
            "GET",
            path,
            auth=auth,
            params=params,
            not_found=QueueNotFound(queue) if queue is not None else None,
        ) as response:
            return self._paginated(
                response,
                IssueTemplateList.model_validate_json(await response.read()).root,
            )

    async def get_issue_template(
        self, template_id: str, *, auth: YandexAuth | None = None
    ) -> IssueTemplate:
        return IssueTemplate.model_validate_json(
            await self._read(
                "GET",
                f"v3/issueTemplates/{template_id}",
                auth=auth,
                not_found=IssueTemplateNotFound(template_id),
            )
        )

    async def get_comment_templates(
        self,
        *,
        queue: str | None = None,
        per_page: int = 50,
        page: int = 1,
        auth: YandexAuth | None = None,
    ) -> PaginatedResult[CommentTemplate]:
        # The queue-scoped endpoint returns the templates of that queue plus the
        # ones not bound to any queue, which are usable in every queue.
        path = (
            "v3/commentTemplates"
            if queue is None
            else f"v3/queues/{queue}/commentTemplates"
        )
        params = {
            "perPage": per_page,
            "page": page,
        }
        async with self._request(
            "GET",
            path,
            auth=auth,
            params=params,
            not_found=QueueNotFound(queue) if queue is not None else None,
        ) as response:
            return self._paginated(
                response,
                CommentTemplateList.model_validate_json(await response.read()).root,
            )

    async def get_comment_template(
        self, template_id: str, *, auth: YandexAuth | None = None
    ) -> CommentTemplate:
        return CommentTemplate.model_validate_json(
            await self._read(
                "GET",
                f"v3/commentTemplates/{template_id}",
                auth=auth,
                not_found=CommentTemplateNotFound(template_id),
            )
        )

    async def issue_get(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> Issue:
        return Issue.model_validate_json(
            await self._read(
                "GET",
                f"v3/issues/{issue_id}",
                auth=auth,
                not_found=IssueNotFound(issue_id),
            )
        )

    async def issues_get_links(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueLink]:
        return IssueLinkList.model_validate_json(
            await self._read(
                "GET",
                f"v3/issues/{issue_id}/links",
                auth=auth,
                not_found=IssueNotFound(issue_id),
            )
        ).root

    async def issue_add_link(
        self,
        issue_id: str,
        *,
        relationship: IssueLinkRelationship,
        issue: str,
        auth: YandexAuth | None = None,
    ) -> IssueLink:
        """Создать связь задачи с другой задачей."""
        body: dict[str, Any] = {"relationship": relationship, "issue": issue}

        return IssueLink.model_validate_json(
            await self._read(
                "POST",
                f"v3/issues/{issue_id}/links",
                auth=auth,
                json=body,
                not_found=IssueNotFound(issue_id),
            )
        )

    async def issue_delete_link(
        self,
        issue_id: str,
        link_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        """Удалить связь задачи с другой задачей."""
        await self._read(
            "DELETE",
            f"v3/issues/{issue_id}/links/{link_id}",
            auth=auth,
            not_found=IssueNotFound(issue_id),
        )

    async def issue_get_comments(
        self,
        issue_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage:
        params: dict[str, Any] = {"perPage": per_page}
        if cursor is not None:
            # `id` is exclusive: the page starts after that comment.
            params["id"] = cursor

        async with self._request(
            "GET",
            f"v3/issues/{issue_id}/comments",
            auth=auth,
            params=params,
            not_found=IssueNotFound(issue_id),
        ) as response:
            comments = IssueCommentList.model_validate_json(await response.read()).root
            return CommentsPage(
                comments=comments,
                next_cursor=self._parse_next_cursor(response),
            )

    async def issue_add_comment(
        self,
        issue_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        markup_type: str | None = None,
        is_add_to_followers: bool = True,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        """Добавить комментарий к задаче."""
        body: dict[str, Any] = {"text": text}
        if summonees is not None:
            body["summonees"] = summonees
        if maillist_summonees is not None:
            body["maillistSummonees"] = maillist_summonees
        if markup_type is not None:
            body["markupType"] = markup_type

        # Параметр опциональный, по умолчанию true на стороне API.
        # Чтобы не менять URL (и поведение по умолчанию), передаём его только при false.
        params = {"isAddToFollowers": "false"} if not is_add_to_followers else None

        return IssueComment.model_validate_json(
            await self._read(
                "POST",
                f"v3/issues/{issue_id}/comments",
                auth=auth,
                params=params,
                json=body,
                not_found=IssueNotFound(issue_id),
            )
        )

    async def issue_update_comment(
        self,
        issue_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        markup_type: str | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        """Изменить комментарий в задаче."""
        body: dict[str, Any] = {"text": text}
        if summonees is not None:
            body["summonees"] = summonees
        if maillist_summonees is not None:
            body["maillistSummonees"] = maillist_summonees
        if markup_type is not None:
            body["markupType"] = markup_type

        return IssueComment.model_validate_json(
            await self._read(
                "PATCH",
                f"v3/issues/{issue_id}/comments/{comment_id}",
                auth=auth,
                json=body,
                not_found=IssueNotFound(issue_id),
            )
        )

    async def issue_delete_comment(
        self,
        issue_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        """Удалить комментарий из задачи."""
        await self._read(
            "DELETE",
            f"v3/issues/{issue_id}/comments/{comment_id}",
            auth=auth,
            not_found=IssueNotFound(issue_id),
        )

    async def issues_find(
        self,
        query: str,
        *,
        per_page: int = 15,
        page: int = 1,
        fields: Sequence[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PaginatedResult[Issue]:
        params: dict[str, Any] = {
            "perPage": per_page,
            "page": page,
        }
        if fields:
            # The endpoint projects server-side, so an unwanted field costs
            # nothing on the wire instead of being fetched and dropped later.
            # Tracker always adds `self`, `id`, `key`, `version` and `favorite`
            # to whatever is asked for.
            params["fields"] = ",".join(fields)

        body: dict[str, Any] = {
            "query": query,
        }

        async with self._request(
            "POST", "v3/issues/_search", auth=auth, params=params, json=body
        ) as response:
            return self._paginated(
                response, IssueList.model_validate_json(await response.read()).root
            )

    @classmethod
    def _paginated(
        cls, response: ClientResponse, values: list[ItemT]
    ) -> PaginatedResult[ItemT]:
        """Pair a decoded page with the totals Tracker reports for the whole query."""
        return PaginatedResult[ItemT](
            values=values,
            hits=cls._parse_int_header(response, "X-Total-Count"),
            pages=cls._parse_int_header(response, "X-Total-Pages"),
        )

    @staticmethod
    def _parse_int_header(response: ClientResponse, name: str) -> int | None:
        """Read an integer pagination total from a response header.

        The totals are advisory: a missing or malformed header just means the
        caller has to fall back to paging until a page comes back empty.
        """
        raw = response.headers.get(name)
        if raw is None:
            return None
        try:
            return int(raw)
        except ValueError:
            logger.warning("non-integer %s response header: %r", name, raw)
            return None

    async def issue_get_worklogs(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[Worklog]:
        return WorklogList.model_validate_json(
            await self._read(
                "GET",
                f"v3/issues/{issue_id}/worklog",
                auth=auth,
                not_found=IssueNotFound(issue_id),
            )
        ).root

    async def issue_add_worklog(
        self,
        issue_id: str,
        *,
        duration: str,
        comment: str | None = None,
        start: datetime.datetime | None = None,
        auth: YandexAuth | None = None,
    ) -> Worklog:
        """Добавить запись трудозатрат (worklog) к задаче.

        Args:
            issue_id: Ключ задачи (например, "QUEUE-123")
            duration: Длительность в формате ISO 8601 (например, "PT1H30M")
            comment: Комментарий к записи
            start: Время начала работ. Если не задано — используется текущее время на стороне Трекера.
            auth: Опциональная auth-структура (OAuth/Org) поверх конфигурации клиента
        """
        body: dict[str, Any] = {"duration": duration}
        if comment is not None:
            body["comment"] = comment
        if start is not None:
            # Если tz отсутствует — считаем, что время задано в UTC.
            body["start"] = _tracker_datetime(start)

        return Worklog.model_validate_json(
            await self._read(
                "POST",
                f"v3/issues/{issue_id}/worklog",
                auth=auth,
                json=body,
                not_found=IssueNotFound(issue_id),
            )
        )

    async def issue_update_worklog(
        self,
        issue_id: str,
        worklog_id: int,
        *,
        duration: str | None = None,
        comment: str | None = None,
        start: datetime.datetime | None = None,
        auth: YandexAuth | None = None,
    ) -> Worklog:
        """Обновить запись трудозатрат (worklog) в задаче."""
        body: dict[str, Any] = {}
        if duration is not None:
            body["duration"] = duration
        if comment is not None:
            body["comment"] = comment
        if start is not None:
            body["start"] = _tracker_datetime(start)

        return Worklog.model_validate_json(
            await self._read(
                "PATCH",
                f"v3/issues/{issue_id}/worklog/{worklog_id}",
                auth=auth,
                json=body,
                not_found=IssueNotFound(issue_id),
            )
        )

    async def issue_delete_worklog(
        self,
        issue_id: str,
        worklog_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        """Удалить запись трудозатрат (worklog) из задачи."""
        await self._read(
            "DELETE",
            f"v3/issues/{issue_id}/worklog/{worklog_id}",
            auth=auth,
            not_found=IssueNotFound(issue_id),
        )

    async def issue_get_attachments(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueAttachment]:
        return IssueAttachmentList.model_validate_json(
            await self._read(
                "GET",
                f"v3/issues/{issue_id}/attachments",
                auth=auth,
                not_found=IssueNotFound(issue_id),
            )
        ).root

    async def users_list(
        self, per_page: int = 50, page: int = 1, *, auth: YandexAuth | None = None
    ) -> PaginatedResult[User]:
        params: dict[str, str | int] = {
            "perPage": per_page,
            "page": page,
        }
        async with self._request(
            "GET", "v3/users", auth=auth, params=params
        ) as response:
            return self._paginated(
                response, UserList.model_validate_json(await response.read()).root
            )

    async def user_get(
        self, user_id: str, *, auth: YandexAuth | None = None
    ) -> User | None:
        # An unknown user is an answer here, not an error, so the 404 is asked
        # for rather than raised.
        async with self._request(
            "GET", f"v3/users/{user_id}", auth=auth, allow_statuses=(404,)
        ) as response:
            if response.status == 404:
                return None
            return User.model_validate_json(await response.read())

    async def user_get_current(self, *, auth: YandexAuth | None = None) -> User:
        return User.model_validate_json(await self._read("GET", "v3/myself", auth=auth))

    async def issue_get_checklist(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[ChecklistItem]:
        return ChecklistItemList.model_validate_json(
            await self._read(
                "GET",
                f"v3/issues/{issue_id}/checklistItems",
                auth=auth,
                not_found=IssueNotFound(issue_id),
            )
        ).root

    @staticmethod
    def _checklist_item_deadline_body(
        deadline: ChecklistItemDeadlineInput | None,
    ) -> dict[str, Any] | None:
        if deadline is None:
            return None
        return {
            "date": _tracker_datetime(deadline.date),
            "deadlineType": deadline.deadline_type,
        }

    async def issue_add_checklist_items(
        self,
        issue_id: str,
        *,
        items: list[ChecklistItemInput],
        auth: YandexAuth | None = None,
    ) -> list[ChecklistItem]:
        """Добавить пункты в чеклист задачи (чеклист создаётся, если его нет).

        `POST .../checklistItems` принимает ровно один пункт за запрос, поэтому
        пункты отправляются последовательно, в переданном порядке; возвращается
        чеклист задачи после добавления последнего пункта.
        """
        if not items:
            return await self.issue_get_checklist(issue_id, auth=auth)

        checklist: list[ChecklistItem] = []

        for added, item in enumerate(items):
            body = self._build_checklist_item_body(
                text=item.text,
                checked=item.checked,
                assignee=item.assignee,
                deadline=self._checklist_item_deadline_body(item.deadline),
            )
            try:
                async with self._request(
                    "POST",
                    f"v3/issues/{issue_id}/checklistItems",
                    auth=auth,
                    json=body,
                    not_found=IssueNotFound(issue_id),
                ) as response:
                    raw = await response.read()
            except Exception as exc:
                # Nothing landed yet on the first item, so let that error speak
                # for itself; past it, say how much of the batch went through.
                if added == 0:
                    raise
                raise ChecklistBatchPartiallyAdded(
                    issue_id, added, len(items), exc
                ) from exc

            # The request succeeded - the item exists now regardless of what
            # follows, so a parse failure here must not be counted as "not
            # added" the way a request failure above is.
            checklist = _IssueChecklist.model_validate_json(raw).checklistItems

        return checklist

    async def issue_update_checklist_item(
        self,
        issue_id: str,
        checklist_item_id: str,
        *,
        text: str | None = None,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: ChecklistItemDeadlineInput | None = None,
        auth: YandexAuth | None = None,
    ) -> list[ChecklistItem]:
        """Изменить один пункт чеклиста задачи.

        Отправляются только переданные поля. Вопреки документации, `text` в теле
        не обязателен: проверено на живом API — `PATCH` с одним лишь `checked`
        (или `assignee`) отвечает 200 и сохраняет текущий текст пункта, так что
        дочитывать и переотправлять его не нужно.
        """
        if text is None and checked is None and assignee is None and deadline is None:
            raise ChecklistItemEmptyUpdate()

        body = self._build_checklist_item_body(
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=self._checklist_item_deadline_body(deadline),
        )
        # Item-scoped path: the 404 means an unknown issue *or* an unknown
        # item, and the caller is told to check both.
        async with self._request(
            "PATCH",
            f"v3/issues/{issue_id}/checklistItems/{checklist_item_id}",
            auth=auth,
            json=body,
            not_found=ChecklistItemNotFound(
                issue_id, checklist_item_id, ambiguous=True
            ),
        ) as response:
            return _IssueChecklist.model_validate_json(
                await response.read()
            ).checklistItems

    async def issue_delete_checklist_item(
        self,
        issue_id: str,
        checklist_item_id: str,
        *,
        auth: YandexAuth | None = None,
    ) -> list[ChecklistItem]:
        """Удалить один пункт из чеклиста задачи."""
        async with self._request(
            "DELETE",
            f"v3/issues/{issue_id}/checklistItems/{checklist_item_id}",
            auth=auth,
            not_found=ChecklistItemNotFound(
                issue_id, checklist_item_id, ambiguous=True
            ),
        ) as response:
            return _IssueChecklist.model_validate_json(
                await response.read()
            ).checklistItems

    async def issues_count(self, query: str, *, auth: YandexAuth | None = None) -> int:
        body: dict[str, Any] = {
            "query": query,
        }

        async with self._request(
            "POST", "v3/issues/_count", auth=auth, json=body
        ) as response:
            return int(await response.text())

    async def issue_create(
        self,
        queue: str,
        summary: str,
        *,
        type: IssueTypeRef | str | int | None = None,
        description: str | None = None,
        markup_type: str | None = None,
        assignee: str | int | None = None,
        priority: IssuePriorityRef | str | int | None = None,
        parent: IssueParentRef | str | None = None,
        sprint: Sequence[IssueSprintRef | str | int] | None = None,
        followers: list[IssueFollowerRef] | None = None,
        components: list[IssueComponentRef] | None = None,
        tags: list[str] | None = None,
        project: IssueProjectRef | None = None,
        auth: YandexAuth | None = None,
        fields: dict[str, Any] | None = None,
    ) -> Issue:
        body: dict[str, Any] = {
            "queue": queue,
            "summary": summary,
        }

        if type is not None:
            body["type"] = _ref_body(type)
        if description is not None:
            body["description"] = description
        if markup_type is not None:
            body["markupType"] = markup_type
        if assignee is not None:
            body["assignee"] = assignee
        if priority is not None:
            body["priority"] = _ref_body(priority)
        if parent is not None:
            body["parent"] = _ref_body(parent)
        if sprint is not None:
            body["sprint"] = [_ref_body(s) for s in sprint]
        if followers is not None:
            body["followers"] = [_ref_body(f) for f in followers]
        if components is not None:
            body["components"] = [c.to_api_value() for c in components]
        if tags is not None:
            body["tags"] = tags
        if project is not None:
            body["project"] = _ref_body(project)

        # Applied last on purpose: an entry here overrides the dedicated
        # parameter of the same name, and an explicit null clears the field.
        if fields:
            body.update(fields)

        return Issue.model_validate_json(
            await self._read("POST", "v3/issues", auth=auth, json=body)
        )

    async def issue_get_transitions(
        self, issue_id: str, *, auth: YandexAuth | None = None
    ) -> list[IssueTransition]:
        return IssueTransitionList.model_validate_json(
            await self._read(
                "GET",
                f"v2/issues/{issue_id}/transitions",
                auth=auth,
                not_found=IssueNotFound(issue_id),
            )
        ).root

    async def issue_get_changelog(
        self,
        issue_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        field: str | None = None,
        type: str | None = None,
        auth: YandexAuth | None = None,
    ) -> ChangelogPage:
        params: dict[str, Any] = {"perPage": per_page}
        if cursor is not None:
            params["id"] = cursor
        if field is not None:
            params["field"] = field
        if type is not None:
            params["type"] = type

        async with self._request(
            "GET",
            f"v3/issues/{issue_id}/changelog",
            auth=auth,
            params=params,
            not_found=IssueNotFound(issue_id),
        ) as response:
            entries = ChangelogList.model_validate_json(await response.read()).root
            return ChangelogPage(
                entries=entries,
                next_cursor=self._parse_next_cursor(response),
            )

    @staticmethod
    def _parse_next_cursor(response: ClientResponse) -> str | None:
        """Extract the next-page cursor from the `Link: rel="next"` response header.

        Yandex Tracker paginates the changelog with an opaque cursor delivered as the
        `id` query parameter of the `next` link, not via the last entry's id.
        """
        next_link = response.links.get("next")
        if next_link is None:
            return None
        next_url = next_link.get("url")
        if not isinstance(next_url, URL):
            return None
        cursor = next_url.query.get("id")
        return str(cursor) if cursor is not None else None

    async def issue_execute_transition(
        self,
        issue_id: str,
        transition_id: str,
        *,
        comment: str | None = None,
        fields: dict[str, str | int | list[str]] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[IssueTransition]:
        body: dict[str, Any] = {}
        if comment is not None:
            body["comment"] = comment
        if fields is not None:
            body.update(fields)

        return IssueTransitionList.model_validate_json(
            await self._read(
                "POST",
                f"v3/issues/{issue_id}/transitions/{transition_id}/_execute",
                auth=auth,
                json=body,
                not_found=IssueNotFound(issue_id),
            )
        ).root

    async def issue_close(
        self,
        issue_id: str,
        resolution_id: str,
        *,
        comment: str | None = None,
        fields: dict[str, str | int | list[str]] | None = None,
        auth: YandexAuth | None = None,
    ) -> list[IssueTransition]:
        # Fetch transitions and statuses in parallel
        async with asyncio.TaskGroup() as tg:
            transitions_task = tg.create_task(
                self.issue_get_transitions(issue_id, auth=auth)
            )
            statuses_task = tg.create_task(self.get_statuses(auth=auth))

        transitions = transitions_task.result()
        statuses = statuses_task.result()

        # Build a map of status key -> status type
        status_type_map: dict[str, str | None] = {
            status.key: status.type for status in statuses
        }

        # Find a transition to a status with type="done"
        done_transition: IssueTransition | None = None
        for transition in transitions:
            if transition.to and transition.to.key:
                status_type = status_type_map.get(transition.to.key)
                if status_type == "done":
                    done_transition = transition
                    break

        if done_transition is None:
            raise ValueError(
                f"No transition to a 'done' status found for issue {issue_id}. "
                f"Available transitions: {[t.id for t in transitions]}."
            )

        if fields is None:
            fields = {}

        fields["resolution"] = resolution_id

        return await self.issue_execute_transition(
            issue_id,
            done_transition.id,
            comment=comment,
            fields=fields,
            auth=auth,
        )

    async def issue_update(
        self,
        issue_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        markup_type: str | None = None,
        parent: IssueParentRef | str | None = None,
        sprint: Sequence[IssueSprintRef | str | int] | None = None,
        type: IssueTypeRef | str | int | None = None,
        priority: IssuePriorityRef | str | int | None = None,
        assignee: str | int | None = None,
        followers: list[IssueFollowerRef] | None = None,
        components: list[IssueComponentRef] | None = None,
        project: IssueProjectRef | None = None,
        attachment_ids: list[str] | None = None,
        description_attachment_ids: list[str] | None = None,
        tags: list[str] | None = None,
        version: int | None = None,
        auth: YandexAuth | None = None,
        fields: dict[str, Any] | None = None,
    ) -> Issue:
        body: dict[str, Any] = {}

        if summary is not None:
            body["summary"] = summary
        if description is not None:
            body["description"] = description
        if markup_type is not None:
            body["markupType"] = markup_type
        if parent is not None:
            body["parent"] = _ref_body(parent)
        if sprint is not None:
            body["sprint"] = [_ref_body(s) for s in sprint]
        if type is not None:
            body["type"] = _ref_body(type)
        if priority is not None:
            body["priority"] = _ref_body(priority)
        if assignee is not None:
            body["assignee"] = assignee
        if followers is not None:
            body["followers"] = [_ref_body(f) for f in followers]
        if components is not None:
            body["components"] = [c.to_api_value() for c in components]
        if project is not None:
            body["project"] = _ref_body(project)
        if attachment_ids is not None:
            body["attachmentIds"] = attachment_ids
        if description_attachment_ids is not None:
            body["descriptionAttachmentIds"] = description_attachment_ids
        if tags is not None:
            body["tags"] = tags

        # Applied last on purpose: an entry here overrides the dedicated
        # parameter of the same name, and an explicit null clears the field.
        if fields:
            body.update(fields)

        params: dict[str, int] = {}
        if version is not None:
            params["version"] = version

        return Issue.model_validate_json(
            await self._read(
                "PATCH",
                f"v3/issues/{issue_id}",
                auth=auth,
                params=params,
                json=body,
                not_found=IssueNotFound(issue_id),
                conflict=IssueVersionConflict(issue_id, version),
            )
        )

    async def issue_move(
        self,
        issue_id: str,
        queue: str,
        *,
        notify: bool = True,
        notify_author: bool = False,
        move_all_fields: bool = False,
        initial_status: bool = False,
        auth: YandexAuth | None = None,
    ) -> Issue:
        params: dict[str, str] = {"queue": queue}
        if not notify:
            params["notify"] = "false"
        if notify_author:
            params["notifyAuthor"] = "true"
        if move_all_fields:
            params["moveAllFields"] = "true"
        if initial_status:
            params["initialStatus"] = "true"

        return Issue.model_validate_json(
            await self._read(
                "POST",
                f"v3/issues/{issue_id}/_move",
                auth=auth,
                params=params,
                not_found=IssueNotFound(issue_id),
            )
        )

    @staticmethod
    def _entity_fields_param(
        entity_type: Literal["project", "portfolio", "goal"],
        fields: list[str] | None,
    ) -> str:
        """Build the `fields` query value for an entity request.

        Yandex Tracker only populates the response's `fields` object with the
        fields explicitly named here, so a per-entity default is applied when
        the caller doesn't pass one. The default sets differ per entity type
        (e.g. `start` is not a valid goal field).
        """
        # An empty list means "nothing selected", which would send `fields=` and
        # come back with an empty `fields` object - fall back to the default.
        if fields:
            return ",".join(fields)
        return DEFAULT_ENTITY_FIELDS_PARAM[entity_type]

    async def _entity_get(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        *,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        params = {"fields": self._entity_fields_param(entity_type, fields)}
        return await self._read(
            "GET", f"v3/entities/{entity_type}/{entity_id}", auth=auth, params=params
        )

    async def _entity_search(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        *,
        input: str | None,
        filter: dict[str, str | list[str]] | None,
        order_by: str | None,
        order_asc: bool | None,
        root_only: bool | None,
        per_page: int,
        page: int,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        params: dict[str, Any] = {
            "perPage": per_page,
            "page": page,
            "fields": self._entity_fields_param(entity_type, fields),
        }

        body: dict[str, Any] = {}
        if input is not None:
            body["input"] = input
        if filter is not None:
            body["filter"] = filter
        if order_by is not None:
            body["orderBy"] = order_by
        if order_asc is not None:
            body["orderAsc"] = order_asc
        if root_only is not None:
            body["rootOnly"] = root_only

        return await self._read(
            "POST",
            f"v3/entities/{entity_type}/_search",
            auth=auth,
            params=params,
            json=body,
        )

    async def project_get(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        return ProjectEntity.model_validate_json(
            await self._entity_get("project", entity_id, fields=fields, auth=auth)
        )

    async def project_find(
        self,
        *,
        input: str | None = None,
        filter: dict[str, str | list[str]] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectSearchResult:
        return ProjectSearchResult.model_validate_json(
            await self._entity_search(
                "project",
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
        )

    async def portfolio_get(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        return PortfolioEntity.model_validate_json(
            await self._entity_get("portfolio", entity_id, fields=fields, auth=auth)
        )

    async def portfolio_find(
        self,
        *,
        input: str | None = None,
        filter: dict[str, str | list[str]] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioSearchResult:
        return PortfolioSearchResult.model_validate_json(
            await self._entity_search(
                "portfolio",
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
        )

    async def goal_get(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalEntity:
        return GoalEntity.model_validate_json(
            await self._entity_get("goal", entity_id, fields=fields, auth=auth)
        )

    async def goal_find(
        self,
        *,
        input: str | None = None,
        filter: dict[str, str | list[str]] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        per_page: int = 50,
        page: int = 1,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalSearchResult:
        return GoalSearchResult.model_validate_json(
            await self._entity_search(
                "goal",
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
        )

    @staticmethod
    def _build_entity_fields_body(
        *,
        summary: str | None,
        description: str | None,
        lead: str | None,
        team_users: list[str] | None,
        clients: list[str] | None,
        followers: list[str] | None,
        start: datetime.date | datetime.datetime | None,
        end: datetime.date | datetime.datetime | None,
        tags: list[str] | None,
        entity_status: str | None,
        parent_entity: EntityParentEntityInput | None,
        team_access: bool | None = None,
    ) -> dict[str, Any]:
        fields_body: dict[str, Any] = {}
        if summary is not None:
            fields_body["summary"] = summary
        if description is not None:
            fields_body["description"] = description
        if lead is not None:
            fields_body["lead"] = lead
        if team_users is not None:
            fields_body["teamUsers"] = team_users
        if clients is not None:
            fields_body["clients"] = clients
        if followers is not None:
            fields_body["followers"] = followers
        if start is not None:
            fields_body["start"] = start.isoformat()
        if end is not None:
            fields_body["end"] = end.isoformat()
        if tags is not None:
            fields_body["tags"] = tags
        if entity_status is not None:
            fields_body["entityStatus"] = entity_status
        if parent_entity is not None:
            fields_body["parentEntity"] = parent_entity.model_dump(exclude_none=True)
        if team_access is not None:
            fields_body["teamAccess"] = team_access
        return fields_body

    async def _entity_create(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        *,
        fields_body: dict[str, Any],
        links: list[ProjectPortfolioLinkInput] | list[GoalLinkInput] | None,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        body: dict[str, Any] = {}
        if fields_body:
            body["fields"] = fields_body
        if links is not None:
            body["links"] = [link.model_dump(exclude_none=True) for link in links]

        return await self._read(
            "POST",
            f"v3/entities/{entity_type}",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
            json=body,
        )

    async def _entity_update(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        *,
        fields_body: dict[str, Any],
        links: list[ProjectPortfolioLinkInput] | list[GoalLinkInput] | None,
        comment: str | None,
        version: int | None,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        # Tracker silently ignores `links` unless the request changes the entity
        # itself, so a links-only update would return 200 having done nothing.
        if links and not fields_body and comment is None:
            raise EntityLinksOnlyUpdate()

        # An update may touch only links and/or add a comment - don't send an empty `fields`.
        body: dict[str, Any] = {}
        if fields_body:
            body["fields"] = fields_body
        if links is not None:
            body["links"] = [link.model_dump(exclude_none=True) for link in links]
        if comment is not None:
            body["comment"] = comment

        params: dict[str, Any] = {
            "fields": self._entity_fields_param(entity_type, fields)
        }
        if version is not None:
            params["version"] = version

        return await self._read(
            "PATCH",
            f"v3/entities/{entity_type}/{entity_id}",
            auth=auth,
            params=params,
            json=body,
        )

    async def _entity_delete(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        *,
        with_board: bool,
        auth: YandexAuth | None,
    ) -> None:
        params = {"withBoard": "true"} if with_board else None
        await self._read(
            "DELETE", f"v3/entities/{entity_type}/{entity_id}", auth=auth, params=params
        )

    async def project_create(
        self,
        *,
        summary: str,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        fields_body = self._build_entity_fields_body(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=start,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
        )
        return ProjectEntity.model_validate_json(
            await self._entity_create(
                "project",
                fields_body=fields_body,
                links=links,
                fields=fields,
                auth=auth,
            )
        )

    async def project_update(
        self,
        entity_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        comment: str | None = None,
        version: int | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        fields_body = self._build_entity_fields_body(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=start,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
        )
        return ProjectEntity.model_validate_json(
            await self._entity_update(
                "project",
                entity_id,
                fields_body=fields_body,
                links=links,
                comment=comment,
                version=version,
                fields=fields,
                auth=auth,
            )
        )

    async def project_delete(
        self,
        entity_id: str,
        *,
        with_board: bool = False,
        auth: YandexAuth | None = None,
    ) -> None:
        await self._entity_delete(
            "project", entity_id, with_board=with_board, auth=auth
        )

    async def portfolio_create(
        self,
        *,
        summary: str,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        fields_body = self._build_entity_fields_body(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=start,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
        )
        return PortfolioEntity.model_validate_json(
            await self._entity_create(
                "portfolio",
                fields_body=fields_body,
                links=links,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_update(
        self,
        entity_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        start: datetime.date | datetime.datetime | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: ProjectPortfolioStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[ProjectPortfolioLinkInput] | None = None,
        comment: str | None = None,
        version: int | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        fields_body = self._build_entity_fields_body(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=start,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
        )
        return PortfolioEntity.model_validate_json(
            await self._entity_update(
                "portfolio",
                entity_id,
                fields_body=fields_body,
                links=links,
                comment=comment,
                version=version,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_delete(
        self,
        entity_id: str,
        *,
        with_board: bool = False,
        auth: YandexAuth | None = None,
    ) -> None:
        await self._entity_delete(
            "portfolio", entity_id, with_board=with_board, auth=auth
        )

    async def goal_create(
        self,
        *,
        summary: str,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: GoalStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[GoalLinkInput] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalEntity:
        fields_body = self._build_entity_fields_body(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=None,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
        )
        return GoalEntity.model_validate_json(
            await self._entity_create(
                "goal", fields_body=fields_body, links=links, fields=fields, auth=auth
            )
        )

    async def goal_update(
        self,
        entity_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        team_users: list[str] | None = None,
        clients: list[str] | None = None,
        followers: list[str] | None = None,
        end: datetime.date | datetime.datetime | None = None,
        tags: list[str] | None = None,
        entity_status: GoalStatus | None = None,
        parent_entity: EntityParentEntityInput | None = None,
        team_access: bool | None = None,
        links: list[GoalLinkInput] | None = None,
        comment: str | None = None,
        version: int | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> GoalEntity:
        fields_body = self._build_entity_fields_body(
            summary=summary,
            description=description,
            lead=lead,
            team_users=team_users,
            clients=clients,
            followers=followers,
            start=None,
            end=end,
            tags=tags,
            entity_status=entity_status,
            parent_entity=parent_entity,
            team_access=team_access,
        )
        return GoalEntity.model_validate_json(
            await self._entity_update(
                "goal",
                entity_id,
                fields_body=fields_body,
                links=links,
                comment=comment,
                version=version,
                fields=fields,
                auth=auth,
            )
        )

    async def goal_delete(
        self,
        entity_id: str,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        # Goals have no board, so `withBoard` is not applicable here.
        await self._entity_delete("goal", entity_id, with_board=False, auth=auth)

    async def _entity_get_comments(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        *,
        per_page: int,
        cursor: str | None,
        auth: YandexAuth | None,
    ) -> CommentsPage:
        params: dict[str, Any] = {"perPage": per_page}
        if cursor is not None:
            # `from` is exclusive: the page starts after that comment.
            params["from"] = cursor

        async with self._request(
            "GET",
            f"v3/entities/{entity_type}/{entity_id}/comments/_relative",
            auth=auth,
            params=params,
        ) as response:
            page = EntityCommentsRelativePage.model_validate_json(await response.read())
            next_cursor: str | None = None
            if page.hasNext and page.comments:
                # `longId` is optional on the comment model; fall back to the
                # numeric id (the API accepts either) so a truncated page is
                # never reported as the complete list.
                last = page.comments[-1]
                next_cursor = last.long_id or str(last.id)
            return CommentsPage(comments=page.comments, next_cursor=next_cursor)

    async def _entity_add_comment(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None,
        maillist_summonees: list[str] | None,
        auth: YandexAuth | None,
    ) -> IssueComment:
        body: dict[str, Any] = {"text": text}
        if summonees is not None:
            body["summonees"] = summonees
        if maillist_summonees is not None:
            body["maillistSummonees"] = maillist_summonees

        return IssueComment.model_validate_json(
            await self._read(
                "POST",
                f"v3/entities/{entity_type}/{entity_id}/comments",
                auth=auth,
                json=body,
            )
        )

    async def _entity_update_comment(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None,
        maillist_summonees: list[str] | None,
        auth: YandexAuth | None,
    ) -> IssueComment:
        body: dict[str, Any] = {"text": text}
        if summonees is not None:
            body["summonees"] = summonees
        if maillist_summonees is not None:
            body["maillistSummonees"] = maillist_summonees

        return IssueComment.model_validate_json(
            await self._read(
                "PATCH",
                f"v3/entities/{entity_type}/{entity_id}/comments/{comment_id}",
                auth=auth,
                json=body,
            )
        )

    async def _entity_delete_comment(
        self,
        entity_type: Literal["project", "portfolio", "goal"],
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None,
    ) -> None:
        await self._read(
            "DELETE",
            f"v3/entities/{entity_type}/{entity_id}/comments/{comment_id}",
            auth=auth,
        )

    async def project_get_comments(
        self,
        entity_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage:
        return await self._entity_get_comments(
            "project", entity_id, per_page=per_page, cursor=cursor, auth=auth
        )

    async def project_add_comment(
        self,
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        return await self._entity_add_comment(
            "project",
            entity_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=auth,
        )

    async def project_update_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        return await self._entity_update_comment(
            "project",
            entity_id,
            comment_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=auth,
        )

    async def project_delete_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        await self._entity_delete_comment("project", entity_id, comment_id, auth=auth)

    async def portfolio_get_comments(
        self,
        entity_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage:
        return await self._entity_get_comments(
            "portfolio", entity_id, per_page=per_page, cursor=cursor, auth=auth
        )

    async def portfolio_add_comment(
        self,
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        return await self._entity_add_comment(
            "portfolio",
            entity_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=auth,
        )

    async def portfolio_update_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        return await self._entity_update_comment(
            "portfolio",
            entity_id,
            comment_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=auth,
        )

    async def portfolio_delete_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        await self._entity_delete_comment("portfolio", entity_id, comment_id, auth=auth)

    async def goal_get_comments(
        self,
        entity_id: str,
        *,
        per_page: int = 50,
        cursor: str | None = None,
        auth: YandexAuth | None = None,
    ) -> CommentsPage:
        return await self._entity_get_comments(
            "goal", entity_id, per_page=per_page, cursor=cursor, auth=auth
        )

    async def goal_add_comment(
        self,
        entity_id: str,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        return await self._entity_add_comment(
            "goal",
            entity_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=auth,
        )

    async def goal_update_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        text: str,
        summonees: list[str] | None = None,
        maillist_summonees: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> IssueComment:
        return await self._entity_update_comment(
            "goal",
            entity_id,
            comment_id,
            text=text,
            summonees=summonees,
            maillist_summonees=maillist_summonees,
            auth=auth,
        )

    async def goal_delete_comment(
        self,
        entity_id: str,
        comment_id: int,
        *,
        auth: YandexAuth | None = None,
    ) -> None:
        await self._entity_delete_comment("goal", entity_id, comment_id, auth=auth)

    @staticmethod
    def _build_checklist_item_body(
        *,
        text: str | None,
        checked: bool | None,
        assignee: str | int | None,
        deadline: dict[str, Any] | None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if text is not None:
            body["text"] = text
        if checked is not None:
            body["checked"] = checked
        if assignee is not None:
            body["assignee"] = assignee
        if deadline is not None:
            body["deadline"] = deadline
        return body

    async def _entity_add_checklist_item(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        *,
        text: str,
        checked: bool | None,
        assignee: str | None,
        deadline: dict[str, Any] | None,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        body = self._build_checklist_item_body(
            text=text, checked=checked, assignee=assignee, deadline=deadline
        )
        return await self._read(
            "POST",
            f"v3/entities/{entity_type}/{entity_id}/checklistItems",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
            json=body,
        )

    async def _entity_update_checklist_item(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        checklist_item_id: str,
        *,
        text: str | None,
        checked: bool | None,
        assignee: str | None,
        deadline: dict[str, Any] | None,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        body = self._build_checklist_item_body(
            text=text, checked=checked, assignee=assignee, deadline=deadline
        )
        return await self._read(
            "PATCH",
            f"v3/entities/{entity_type}/{entity_id}/checklistItems/{checklist_item_id}",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
            json=body,
        )

    async def _entity_move_checklist_item(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        checklist_item_id: str,
        *,
        before: str,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        return await self._read(
            "POST",
            f"v3/entities/{entity_type}/{entity_id}/checklistItems/{checklist_item_id}/_move",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
            json={"before": before},
        )

    async def _entity_delete_checklist_item(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        checklist_item_id: str,
        *,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        return await self._read(
            "DELETE",
            f"v3/entities/{entity_type}/{entity_id}/checklistItems/{checklist_item_id}",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
        )

    async def _entity_update_checklist(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        *,
        items: list[EntityChecklistItemUpdateInput],
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        body = [item.model_dump(exclude_none=True) for item in items]
        return await self._read(
            "PATCH",
            f"v3/entities/{entity_type}/{entity_id}/checklistItems",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
            json=body,
        )

    @staticmethod
    def _checklist_item_to_update_input(
        item: ChecklistItem,
    ) -> EntityChecklistItemUpdateInput:
        deadline: dict[str, Any] | None = None
        if item.deadline is not None:
            deadline = {
                "date": _tracker_datetime(item.deadline.date),
                "deadlineType": item.deadline.deadline_type,
            }
        return EntityChecklistItemUpdateInput(
            id=item.id,
            text=item.text,
            checked=item.checked,
            assignee=(item.assignee.id if item.assignee is not None else None),
            deadline=deadline,
        )

    async def _reconcile_checklist_update(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        *,
        items: list[EntityChecklistItemUpdateInput],
        auth: YandexAuth | None,
    ) -> list[EntityChecklistItemUpdateInput]:
        """Fill in the rest of the checklist so a caller can send just the items it wants to change.

        `PATCH .../checklistItems` edits every item in the array it is given and
        rejects the request outright if the array's length does not match the
        entity's current item count - verified against the live API, sending a
        subset (to drop items) or an extra item (to add one) both answer with an
        opaque 500. Fetching the current checklist first and resending every item
        - untouched ones verbatim, requested ones with the caller's overrides
        applied - makes a true partial update possible without the caller having
        to know about this quirk.
        """
        current_raw = await self._entity_get(
            entity_type, entity_id, fields=["checklistItems"], auth=auth
        )
        current = _ChecklistSnapshot.model_validate_json(current_raw)
        current_by_id = {item.id: item for item in current.fields.checklistItems}

        overrides = {item.id: item for item in items}
        for item_id in overrides:
            if item_id not in current_by_id:
                raise ChecklistItemNotFound(entity_id, item_id)

        merged: list[EntityChecklistItemUpdateInput] = []
        for item_id, current_item in current_by_id.items():
            override = overrides.get(item_id)
            if override is None:
                merged.append(self._checklist_item_to_update_input(current_item))
                continue
            base = self._checklist_item_to_update_input(current_item)
            merged.append(
                EntityChecklistItemUpdateInput(
                    id=item_id,
                    text=override.text,
                    checked=(
                        override.checked
                        if override.checked is not None
                        else base.checked
                    ),
                    assignee=(
                        override.assignee
                        if override.assignee is not None
                        else base.assignee
                    ),
                    deadline=(
                        override.deadline
                        if override.deadline is not None
                        else base.deadline
                    ),
                )
            )
        return merged

    async def _entity_delete_checklist(
        self,
        entity_type: Literal["project", "portfolio"],
        entity_id: str,
        *,
        fields: list[str] | None,
        auth: YandexAuth | None,
    ) -> bytes:
        return await self._read(
            "DELETE",
            f"v3/entities/{entity_type}/{entity_id}/checklistItems",
            auth=auth,
            params={"fields": self._entity_fields_param(entity_type, fields)},
        )

    async def project_add_checklist_item(
        self,
        entity_id: str,
        *,
        text: str,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        return ProjectEntity.model_validate_json(
            await self._entity_add_checklist_item(
                "project",
                entity_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )
        )

    async def project_update_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        text: str | None = None,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        return ProjectEntity.model_validate_json(
            await self._entity_update_checklist_item(
                "project",
                entity_id,
                checklist_item_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )
        )

    async def project_move_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        before: str,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        return ProjectEntity.model_validate_json(
            await self._entity_move_checklist_item(
                "project",
                entity_id,
                checklist_item_id,
                before=before,
                fields=fields,
                auth=auth,
            )
        )

    async def project_delete_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        return ProjectEntity.model_validate_json(
            await self._entity_delete_checklist_item(
                "project",
                entity_id,
                checklist_item_id,
                fields=fields,
                auth=auth,
            )
        )

    async def project_update_checklist(
        self,
        entity_id: str,
        *,
        items: list[EntityChecklistItemUpdateInput],
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        merged_items = await self._reconcile_checklist_update(
            "project", entity_id, items=items, auth=auth
        )
        return ProjectEntity.model_validate_json(
            await self._entity_update_checklist(
                "project",
                entity_id,
                items=merged_items,
                fields=fields,
                auth=auth,
            )
        )

    async def project_delete_checklist(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> ProjectEntity:
        return ProjectEntity.model_validate_json(
            await self._entity_delete_checklist(
                "project", entity_id, fields=fields, auth=auth
            )
        )

    async def portfolio_add_checklist_item(
        self,
        entity_id: str,
        *,
        text: str,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        return PortfolioEntity.model_validate_json(
            await self._entity_add_checklist_item(
                "portfolio",
                entity_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_update_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        text: str | None = None,
        checked: bool | None = None,
        assignee: str | None = None,
        deadline: dict[str, Any] | None = None,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        return PortfolioEntity.model_validate_json(
            await self._entity_update_checklist_item(
                "portfolio",
                entity_id,
                checklist_item_id,
                text=text,
                checked=checked,
                assignee=assignee,
                deadline=deadline,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_move_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        before: str,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        return PortfolioEntity.model_validate_json(
            await self._entity_move_checklist_item(
                "portfolio",
                entity_id,
                checklist_item_id,
                before=before,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_delete_checklist_item(
        self,
        entity_id: str,
        checklist_item_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        return PortfolioEntity.model_validate_json(
            await self._entity_delete_checklist_item(
                "portfolio",
                entity_id,
                checklist_item_id,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_update_checklist(
        self,
        entity_id: str,
        *,
        items: list[EntityChecklistItemUpdateInput],
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        merged_items = await self._reconcile_checklist_update(
            "portfolio", entity_id, items=items, auth=auth
        )
        return PortfolioEntity.model_validate_json(
            await self._entity_update_checklist(
                "portfolio",
                entity_id,
                items=merged_items,
                fields=fields,
                auth=auth,
            )
        )

    async def portfolio_delete_checklist(
        self,
        entity_id: str,
        *,
        fields: list[str] | None = None,
        auth: YandexAuth | None = None,
    ) -> PortfolioEntity:
        return PortfolioEntity.model_validate_json(
            await self._entity_delete_checklist(
                "portfolio", entity_id, fields=fields, auth=auth
            )
        )

    async def boards_list(
        self,
        *,
        per_page: int = 100,
        cursor: int | None = None,
        auth: YandexAuth | None = None,
    ) -> list[Board]:
        """One page of boards, ascending by id.

        `cursor` is the id of the last board of the previous page and is
        exclusive; a page shorter than `per_page` is the last one.

        This is the only way boards are read. `/v3/boards` returns the whole
        organization in one response - 1.4 MB and 7-16s for 415 boards, in a
        different order every call - and no timeout fits that, because the
        request grows with the Tracker it is pointed at: generous for one
        organization is not enough for the next. A page is bounded by `per_page`
        instead, so what the budget has to cover stops depending on how large
        the organization is. It does not make the API's own variance go away,
        which is what `TRACKER_API_TIMEOUT` and `TrackerAPITimeout` are for.
        """
        params: dict[str, Any] = {"perPage": min(per_page, BOARDS_PAGE_MAX)}
        if cursor is not None:
            params["id"] = cursor

        return BoardList.model_validate_json(
            await self._read("GET", "v3/boards/_paginate", auth=auth, params=params)
        ).root

    async def board_get(
        self, board_id: int, *, auth: YandexAuth | None = None
    ) -> Board:
        return Board.model_validate_json(
            await self._read(
                "GET",
                f"v3/boards/{board_id}",
                auth=auth,
                not_found=BoardNotFound(board_id),
            )
        )

    async def board_get_columns(
        self, board_id: int, *, auth: YandexAuth | None = None
    ) -> list[BoardColumnDetail]:
        return BoardColumnList.model_validate_json(
            await self._read(
                "GET",
                f"v3/boards/{board_id}/columns",
                auth=auth,
                not_found=BoardNotFound(board_id),
            )
        ).root

    async def board_get_sprints(
        self, board_id: int, *, auth: YandexAuth | None = None
    ) -> list[Sprint]:
        # A board that is not a scrum board answers 400 with "У доски этого типа
        # не может быть спринтов." - that explanation only reaches the caller
        # because `_request` puts every response through `_raise_for_status`.
        return SprintList.model_validate_json(
            await self._read(
                "GET",
                f"v3/boards/{board_id}/sprints",
                auth=auth,
                not_found=BoardNotFound(board_id),
            )
        ).root
