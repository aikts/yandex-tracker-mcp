import pytest

from mcp_tracker.tracker.proto.types.fields import FieldSchema, GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueTransition,
    LinkTypeReference,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.refs import (
    IssueReference,
    IssueTypeReference,
    PriorityReference,
    StatusReference,
    UserReference,
)
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.users import User


# Queue fixtures
@pytest.fixture
def sample_queue() -> Queue:
    """Sample queue for testing."""
    return Queue.model_construct(
        id=1,
        key="TEST",
        name="Test Queue",
        description="A test queue for unit testing",
        defaultType=IssueTypeReference.model_construct(
            id="1",
            key="task",
            display="Task",
        ),
        defaultPriority=PriorityReference.model_construct(
            id="3",
            key="normal",
            display="Normal",
        ),
    )


@pytest.fixture
def sample_queues(sample_queue: Queue) -> list[Queue]:
    """Sample list of queues for testing."""
    return [
        sample_queue,
        Queue.model_construct(
            id=2,
            key="DEV",
            name="Development Queue",
        ),
        Queue.model_construct(
            id=3,
            key="SUPPORT",
            name="Support Queue",
        ),
    ]


@pytest.fixture
def sample_queue_tags() -> list[str]:
    """Sample queue tags for testing."""
    return ["bug", "feature", "enhancement", "documentation"]


@pytest.fixture
def sample_queue_versions() -> list[QueueVersion]:
    """Sample queue versions for testing."""
    return [
        QueueVersion.model_construct(
            id=1,
            version=1,
            name="1.0.0",
            description="Initial release",
            released=True,
            archived=False,
        ),
        QueueVersion.model_construct(
            id=2,
            version=1,
            name="2.0.0",
            description="Major update",
            released=False,
            archived=False,
        ),
    ]


# Field fixtures
@pytest.fixture
def sample_global_field() -> GlobalField:
    """Sample global field for testing."""
    return GlobalField.model_construct(
        id="summary",
        name="Summary",
        key="summary",
        version=1,
        schema_=FieldSchema(type="string", required=True),
        readonly=False,
    )


@pytest.fixture
def sample_global_fields(sample_global_field: GlobalField) -> list[GlobalField]:
    """Sample list of global fields for testing."""
    return [
        sample_global_field,
        GlobalField.model_construct(
            id="description",
            name="Description",
            key="description",
            version=1,
            schema_=FieldSchema(type="string", required=False),
            readonly=False,
        ),
        GlobalField.model_construct(
            id="assignee",
            name="Assignee",
            key="assignee",
            version=1,
            schema_=FieldSchema(type="user", required=False),
            readonly=False,
        ),
    ]


@pytest.fixture
def sample_local_field() -> LocalField:
    """Sample local field for testing."""
    return LocalField.model_construct(
        id="custom-field",
        name="Custom Field",
        key="customField",
        version=1,
        schema_=FieldSchema(type="string", required=False),
        description="A custom local field",
    )


@pytest.fixture
def sample_local_fields(sample_local_field: LocalField) -> list[LocalField]:
    """Sample list of local fields for testing."""
    return [sample_local_field]


# Status fixtures
@pytest.fixture
def sample_status() -> Status:
    """Sample status for testing."""
    return Status.model_construct(
        version=1,
        key="open",
        name="Open",
        description="Issue is open",
        order=1,
        type="new",
    )


@pytest.fixture
def sample_statuses(sample_status: Status) -> list[Status]:
    """Sample list of statuses for testing."""
    return [
        sample_status,
        Status.model_construct(
            version=1,
            key="inProgress",
            name="In Progress",
            order=2,
            type="inProgress",
        ),
        Status.model_construct(
            version=1,
            key="closed",
            name="Closed",
            order=3,
            type="done",
        ),
    ]


# Issue type fixtures
@pytest.fixture
def sample_issue_type() -> IssueType:
    """Sample issue type for testing."""
    return IssueType.model_construct(
        id=1,
        version=1,
        key="task",
        name="Task",
        description="A task issue type",
    )


@pytest.fixture
def sample_issue_types(sample_issue_type: IssueType) -> list[IssueType]:
    """Sample list of issue types for testing."""
    return [
        sample_issue_type,
        IssueType.model_construct(
            id=2,
            version=1,
            key="bug",
            name="Bug",
            description="A bug issue type",
        ),
        IssueType.model_construct(
            id=3,
            version=1,
            key="story",
            name="Story",
            description="A user story",
        ),
    ]


# Priority fixtures
@pytest.fixture
def sample_priority() -> Priority:
    """Sample priority for testing."""
    return Priority.model_construct(
        version=1,
        key="normal",
        name="Normal",
        order=3,
    )


@pytest.fixture
def sample_priorities(sample_priority: Priority) -> list[Priority]:
    """Sample list of priorities for testing."""
    return [
        Priority.model_construct(
            version=1,
            key="critical",
            name="Critical",
            order=1,
        ),
        Priority.model_construct(
            version=1,
            key="high",
            name="High",
            order=2,
        ),
        sample_priority,
    ]


# Resolution fixtures
@pytest.fixture
def sample_resolution() -> Resolution:
    """Sample resolution for testing."""
    return Resolution.model_construct(
        id=1,
        key="fixed",
        version=1,
        name="Fixed",
        description="Issue has been fixed",
        order=1,
    )


@pytest.fixture
def sample_resolutions(sample_resolution: Resolution) -> list[Resolution]:
    """Sample list of resolutions for testing."""
    return [
        sample_resolution,
        Resolution.model_construct(
            id=2,
            key="wontFix",
            version=1,
            name="Won't Fix",
            description="Issue will not be fixed",
            order=2,
        ),
        Resolution.model_construct(
            id=3,
            key="duplicate",
            version=1,
            name="Duplicate",
            description="Issue is a duplicate",
            order=3,
        ),
    ]


# Issue fixtures
@pytest.fixture
def sample_issue() -> Issue:
    """Sample issue for testing."""
    return Issue.model_construct(
        id="593cd211ef7e8a33abcd1234",
        version=1,
        key="TEST-123",
        summary="Test issue summary",
        description="Test issue description with detailed content.",
        type=IssueTypeReference.model_construct(
            id="1",
            key="task",
            display="Task",
        ),
        status=StatusReference.model_construct(
            id="1",
            key="open",
            display="Open",
        ),
        priority=PriorityReference.model_construct(
            id="3",
            key="normal",
            display="Normal",
        ),
        createdBy=UserReference.model_construct(
            id="user123",
            display="Test User",
        ),
    )


@pytest.fixture
def sample_issues(sample_issue: Issue) -> list[Issue]:
    """Sample list of issues for testing."""
    return [
        sample_issue,
        Issue.model_construct(
            id="593cd211ef7e8a33abcd1235",
            version=1,
            key="TEST-124",
            summary="Another test issue",
            status=StatusReference.model_construct(
                id="2",
                key="inProgress",
                display="In Progress",
            ),
        ),
        Issue.model_construct(
            id="593cd211ef7e8a33abcd1236",
            version=2,
            key="TEST-125",
            summary="Closed issue",
            status=StatusReference.model_construct(
                id="3",
                key="closed",
                display="Closed",
            ),
        ),
    ]


# Issue comment fixtures
@pytest.fixture
def sample_comment() -> IssueComment:
    """Sample issue comment for testing."""
    return IssueComment.model_construct(
        id=1,
        text="This is a test comment",
        createdBy=UserReference.model_construct(
            id="user123",
            display="Test User",
        ),
    )


@pytest.fixture
def sample_comments(sample_comment: IssueComment) -> list[IssueComment]:
    """Sample list of issue comments for testing."""
    return [
        sample_comment,
        IssueComment.model_construct(
            id=2,
            text="Another comment on the issue",
        ),
    ]


# Issue link fixtures
@pytest.fixture
def sample_link() -> IssueLink:
    """Sample issue link for testing."""
    return IssueLink.model_construct(
        id=1,
        direction="outward",
        type=LinkTypeReference.model_construct(
            id="relates",
            inward="is related to",
            outward="relates to",
        ),
        object=IssueReference.model_construct(
            id="593cd211ef7e8a33abcd9999",
            key="TEST-456",
            display="TEST-456",
        ),
    )


@pytest.fixture
def sample_links(sample_link: IssueLink) -> list[IssueLink]:
    """Sample list of issue links for testing."""
    return [sample_link]


# Worklog fixtures
@pytest.fixture
def sample_worklog() -> Worklog:
    """Sample worklog for testing."""
    return Worklog.model_construct(
        id=1,
        comment="Worked on implementation",
        createdBy=UserReference.model_construct(
            id="user123",
            display="Test User",
        ),
    )


@pytest.fixture
def sample_worklogs(sample_worklog: Worklog) -> list[Worklog]:
    """Sample list of worklogs for testing."""
    return [sample_worklog]


# Attachment fixtures
@pytest.fixture
def sample_attachment() -> IssueAttachment:
    """Sample issue attachment for testing."""
    return IssueAttachment.model_construct(
        id="attachment-1",
        name="screenshot.png",
        content="https://tracker.yandex.net/attachments/1",
        size=102400,
        mimetype="image/png",
        createdBy=UserReference.model_construct(
            id="user123",
            display="Test User",
        ),
    )


@pytest.fixture
def sample_attachments(sample_attachment: IssueAttachment) -> list[IssueAttachment]:
    """Sample list of attachments for testing."""
    return [sample_attachment]


# Checklist fixtures
@pytest.fixture
def sample_checklist_item() -> ChecklistItem:
    """Sample checklist item for testing."""
    return ChecklistItem.model_construct(
        id="checklist-1",
        text="Complete the implementation",
        checked=False,
    )


@pytest.fixture
def sample_checklist(sample_checklist_item: ChecklistItem) -> list[ChecklistItem]:
    """Sample checklist for testing."""
    return [
        sample_checklist_item,
        ChecklistItem.model_construct(
            id="checklist-2",
            text="Write unit tests",
            checked=True,
        ),
    ]


# Transition fixtures
@pytest.fixture
def sample_transition() -> IssueTransition:
    """Sample issue transition for testing."""
    return IssueTransition.model_construct(
        id="start_progress",
        display="Start Progress",
        to=StatusReference.model_construct(
            id="2",
            key="inProgress",
            display="In Progress",
        ),
    )


@pytest.fixture
def sample_transitions(sample_transition: IssueTransition) -> list[IssueTransition]:
    """Sample list of transitions for testing."""
    return [
        sample_transition,
        IssueTransition.model_construct(
            id="resolve",
            display="Resolve",
            to=StatusReference.model_construct(
                id="3",
                key="closed",
                display="Closed",
            ),
        ),
    ]


# User fixtures
@pytest.fixture
def sample_user() -> User:
    """Sample user for testing."""
    return User.model_construct(
        uid=1234567890,
        login="testuser",
        first_name="Test",
        last_name="User",
        display="Test User",
        email="testuser@example.com",
        external=False,
        dismissed=False,
    )


@pytest.fixture
def sample_users(sample_user: User) -> list[User]:
    """Sample list of users for testing."""
    return [
        sample_user,
        User.model_construct(
            uid=9876543210,
            login="anotheruser",
            first_name="Another",
            last_name="User",
            display="Another User",
            email="another@example.com",
            external=False,
            dismissed=False,
        ),
        User.model_construct(
            uid=5555555555,
            login="manager",
            first_name="Project",
            last_name="Manager",
            display="Project Manager",
            email="manager@example.com",
            external=False,
            dismissed=False,
        ),
    ]
