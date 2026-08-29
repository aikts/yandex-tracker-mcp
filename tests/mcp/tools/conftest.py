import datetime

import pytest

from mcp_tracker.tracker.proto.types.boards import (
    Board,
    BoardAutoFilterSettings,
    BoardColumn,
    BoardColumnDetail,
    BoardColumnStatus,
    BoardFilterField,
    BoardFilterFieldValue,
    BoardFilterSettings,
    BoardFilterValueRef,
    BoardLiveFilter,
    Sprint,
)
from mcp_tracker.tracker.proto.types.entities import (
    GoalEntity,
    GoalFields,
    GoalSearchResult,
    PortfolioEntity,
    PortfolioFields,
    PortfolioSearchResult,
    ProjectEntity,
    ProjectFields,
    ProjectSearchResult,
)
from mcp_tracker.tracker.proto.types.fields import FieldSchema, GlobalField, LocalField
from mcp_tracker.tracker.proto.types.issue_types import IssueType
from mcp_tracker.tracker.proto.types.issues import (
    ChangelogEntry,
    ChangelogFieldChange,
    ChangelogFieldReference,
    ChangelogPage,
    ChecklistItem,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueTransition,
    LinkTypeReference,
    MaillistReference,
    Worklog,
)
from mcp_tracker.tracker.proto.types.priorities import Priority
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from mcp_tracker.tracker.proto.types.refs import (
    BoardReference,
    IssueReference,
    IssueTypeReference,
    PriorityReference,
    QueueReference,
    StatusReference,
    UserReference,
)
from mcp_tracker.tracker.proto.types.resolutions import Resolution
from mcp_tracker.tracker.proto.types.statuses import Status
from mcp_tracker.tracker.proto.types.templates import CommentTemplate, IssueTemplate
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
        id=3,
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
            id=4,
            version=1,
            key="critical",
            name="Critical",
            order=1,
        ),
        Priority.model_construct(
            id=2,
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


# Changelog fixtures
@pytest.fixture
def sample_changelog_entry() -> ChangelogEntry:
    """Sample issue changelog entry for testing."""
    return ChangelogEntry.model_construct(
        id="5f2c0000000000000000abcd",
        type="IssueWorkflow",
        transport="front",
        updated_by=UserReference.model_construct(id="user123", display="Test User"),
        fields=[
            ChangelogFieldChange.model_construct(
                field=ChangelogFieldReference.model_construct(
                    id="status", display="Status"
                ),
                from_={"id": "1", "key": "open", "display": "Open"},
                to={"id": "2", "key": "inProgress", "display": "In Progress"},
            )
        ],
    )


@pytest.fixture
def sample_changelog(sample_changelog_entry: ChangelogEntry) -> ChangelogPage:
    """Sample changelog page (with a next cursor) for testing."""
    return ChangelogPage(
        entries=[
            sample_changelog_entry,
            ChangelogEntry.model_construct(
                id="5f2c0000000000000000ef01",
                type="IssueUpdated",
                transport="front",
                updated_by=UserReference.model_construct(
                    id="user123", display="Test User"
                ),
                fields=[
                    ChangelogFieldChange.model_construct(
                        field=ChangelogFieldReference.model_construct(
                            id="assignee", display="Assignee"
                        ),
                        from_=None,
                        to={"id": "user456", "display": "Another User"},
                    )
                ],
            ),
        ],
        next_cursor="5f2c0000000000000000ef01",
    )


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


# Board fixtures
@pytest.fixture
def sample_board() -> Board:
    """Sample agile board for testing."""
    return Board.model_construct(
        id=1,
        version=1,
        name="Development board",
        createdBy=UserReference.model_construct(
            id="user123",
            display="Test User",
        ),
        columns=[
            BoardColumn.model_construct(id="1", display="Open"),
            BoardColumn.model_construct(id="2", display="In Progress"),
        ],
    )


@pytest.fixture
def sample_board_with_settings() -> Board:
    """A board carrying the settings `board_get` is there to expose."""
    return Board.model_construct(
        id=1,
        version=1,
        name="Development board",
        useRanking=False,
        estimateBy=BoardFilterValueRef.model_construct(
            id="storyPoints", display="Story Points"
        ),
        autoFilterSettings=BoardAutoFilterSettings.model_construct(
            addFilterSettings=BoardFilterSettings.model_construct(
                enabled=True,
                liveFilter=BoardLiveFilter.model_construct(
                    fieldValues=[
                        BoardFilterField.model_construct(
                            id="queue",
                            key="queue",
                            name="Очередь",
                            fieldType="queue",
                            value=[
                                BoardFilterFieldValue.model_construct(
                                    fixed=BoardFilterValueRef.model_construct(
                                        id="88", key="LEVELARM", display="Строители"
                                    ),
                                    invert=False,
                                )
                            ],
                        )
                    ]
                ),
            )
        ),
    )


def make_board_on_queues(
    board_id: int,
    name: str,
    *queues: str,
    invert: bool = False,
    field_id: str | None = "queue",
    field_key: str | None = "queue",
) -> Board:
    """A board whose auto-filter collects the given queues.

    `field_id` / `field_key` are how the filter names the queue field. Captured
    payloads carry both, so either alone has to be enough to recognise it.
    """
    return Board.model_construct(
        id=board_id,
        name=name,
        autoFilterSettings=BoardAutoFilterSettings.model_construct(
            addFilterSettings=BoardFilterSettings.model_construct(
                liveFilter=BoardLiveFilter.model_construct(
                    fieldValues=[
                        BoardFilterField.model_construct(
                            id=field_id,
                            key=field_key,
                            value=[
                                BoardFilterFieldValue.model_construct(
                                    fixed=BoardFilterValueRef.model_construct(
                                        id=str(i), key=queue, display=queue
                                    ),
                                    invert=invert,
                                )
                                for i, queue in enumerate(queues)
                            ],
                        )
                    ]
                )
            )
        ),
    )


@pytest.fixture
def boards_across_queues() -> list[Board]:
    """A listing mixing boards bound to queues with boards that name none."""
    return [
        make_board_on_queues(1, "Level ARM", "LEVELARM"),
        make_board_on_queues(2, "Smartbot", "SMARTBOTSITE", "SMARTBOTGOALS"),
        make_board_on_queues(3, "Not Level ARM", "LEVELARM", invert=True),
        Board.model_construct(id=4, name="Личная доска"),
    ]


@pytest.fixture
def sample_board_columns() -> list[BoardColumnDetail]:
    """Columns as `GET /v3/boards/{id}/columns` returns them, with statuses."""
    return [
        BoardColumnDetail.model_construct(
            id=1,
            name="Открыт",
            statuses=[
                BoardColumnStatus.model_construct(id="1", key="open", display="Открыт"),
                BoardColumnStatus.model_construct(id="20", key="new", display="Новый"),
            ],
        ),
        BoardColumnDetail.model_construct(
            id=2,
            name="В работе",
            statuses=[
                BoardColumnStatus.model_construct(
                    id="3", key="inProgress", display="В работе"
                )
            ],
        ),
    ]


@pytest.fixture
def sample_boards(sample_board: Board) -> list[Board]:
    """Sample list of agile boards for testing."""
    return [
        sample_board,
        Board.model_construct(
            id=2,
            version=1,
            name="Support board",
        ),
    ]


# Sprint fixtures
@pytest.fixture
def sample_sprint() -> Sprint:
    """Sample sprint (currently running) for testing."""
    return Sprint.model_construct(
        id=44,
        version=1,
        name="Sprint 1",
        board=BoardReference.model_construct(id="1", display="Development board"),
        status="in_progress",
        archived=False,
        startDate=datetime.date(2015, 6, 1),
        endDate=datetime.date(2015, 6, 14),
    )


@pytest.fixture
def sample_sprints(sample_sprint: Sprint) -> list[Sprint]:
    """Sample list of sprints for testing."""
    return [
        Sprint.model_construct(
            id=43,
            version=1,
            name="Sprint 0",
            board=BoardReference.model_construct(id="1", display="Development board"),
            status="released",
            archived=False,
        ),
        sample_sprint,
        Sprint.model_construct(
            id=45,
            version=1,
            name="Sprint 2",
            board=BoardReference.model_construct(id="1", display="Development board"),
            status="draft",
            archived=False,
        ),
    ]


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


# Issue template fixtures
@pytest.fixture
def sample_issue_template() -> IssueTemplate:
    """Sample issue template bound to the TEST queue."""
    return IssueTemplate.model_construct(
        id="1",
        version=2,
        name="Bug report",
        queue=QueueReference.model_construct(id="1", key="TEST", display="Test Queue"),
        fieldTemplates={
            "summary": "Bug: ",
            "description": "## Steps to reproduce\n\n## Expected\n\n## Actual",
        },
    )


@pytest.fixture
def sample_issue_templates(sample_issue_template: IssueTemplate) -> list[IssueTemplate]:
    """Issue templates spanning an allowed queue, a restricted queue and no queue."""
    return [
        sample_issue_template,
        IssueTemplate.model_construct(
            id="2",
            version=1,
            name="Incident",
            queue=QueueReference.model_construct(
                id="2", key="ALLOWED", display="Allowed Queue"
            ),
            fieldTemplates={"summary": "Incident: "},
        ),
        IssueTemplate.model_construct(
            id="3",
            version=1,
            name="Personal template",
            queue=None,
            fieldTemplates={"summary": "Note: "},
        ),
    ]


# Comment template fixtures
@pytest.fixture
def sample_comment_template() -> CommentTemplate:
    """Sample comment template bound to the TEST queue."""
    return CommentTemplate.model_construct(
        id="1",
        version=2,
        name="Incident acknowledged",
        description="First reply on an incident",
        template="We received your report and started the investigation.",
        summonees=[UserReference.model_construct(id="1", display="Ivan Ivanov")],
        maillistSummonees=[
            MaillistReference.model_construct(id="duty@example.com", display="Duty")
        ],
        queue=QueueReference.model_construct(id="1", key="TEST", display="Test Queue"),
    )


@pytest.fixture
def sample_comment_templates(
    sample_comment_template: CommentTemplate,
) -> list[CommentTemplate]:
    """Comment templates spanning an allowed queue, a restricted queue and no queue."""
    return [
        sample_comment_template,
        CommentTemplate.model_construct(
            id="2",
            version=1,
            name="Escalation",
            template="Escalating to the duty engineer.",
            queue=QueueReference.model_construct(
                id="2", key="ALLOWED", display="Allowed Queue"
            ),
        ),
        CommentTemplate.model_construct(
            id="3",
            version=1,
            name="Personal reply",
            template="Thanks, taking a look.",
            queue=None,
        ),
    ]


# Entity (project/portfolio/goal) fixtures
@pytest.fixture
def sample_project() -> ProjectEntity:
    """Sample project entity for testing."""
    return ProjectEntity.model_construct(
        id="abc123",
        shortId=1,
        version=1,
        entityType="project",
        fields=ProjectFields.model_construct(
            summary="Test Project",
            description="A test project for unit testing",
            entityStatus="in_progress",
        ),
    )


@pytest.fixture
def sample_projects(sample_project: ProjectEntity) -> ProjectSearchResult:
    """Sample project search result for testing."""
    return ProjectSearchResult.model_construct(
        hits=1,
        pages=1,
        values=[sample_project],
    )


@pytest.fixture
def sample_portfolio() -> PortfolioEntity:
    """Sample portfolio entity for testing."""
    return PortfolioEntity.model_construct(
        id="def456",
        shortId=2,
        version=1,
        entityType="portfolio",
        fields=PortfolioFields.model_construct(
            summary="Test Portfolio",
            description="A test portfolio for unit testing",
            entityStatus="in_progress",
        ),
    )


@pytest.fixture
def sample_portfolios(sample_portfolio: PortfolioEntity) -> PortfolioSearchResult:
    """Sample portfolio search result for testing."""
    return PortfolioSearchResult.model_construct(
        hits=1,
        pages=1,
        values=[sample_portfolio],
    )


@pytest.fixture
def sample_goal() -> GoalEntity:
    """Sample goal entity for testing."""
    return GoalEntity.model_construct(
        id="ghi789",
        shortId=3,
        version=1,
        entityType="goal",
        fields=GoalFields.model_construct(
            summary="Test Goal",
            description="A test goal for unit testing",
            entityStatus="according_to_plan",
        ),
    )


@pytest.fixture
def sample_goals(sample_goal: GoalEntity) -> GoalSearchResult:
    """Sample goal search result for testing."""
    return GoalSearchResult.model_construct(
        hits=1,
        pages=1,
        values=[sample_goal],
    )
