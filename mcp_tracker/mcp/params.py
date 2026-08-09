import datetime
from typing import Annotated, get_args

from pydantic import Field

from mcp_tracker.tracker.proto.types.entities import (
    DEFAULT_ENTITY_FIELDS,
    GoalFieldsEnum,
    GoalLinkRelationship,
    GoalStatus,
    PortfolioFieldsEnum,
    ProjectFieldsEnum,
    ProjectPortfolioLinkRelationship,
    ProjectPortfolioStatus,
)
from mcp_tracker.tracker.proto.types.inputs import (
    EntityParentEntityInput,
    GoalLinkInput,
    IssueComponentRef,
    IssueFollowerRef,
    IssueParentRef,
    IssueProjectRef,
    IssueSprintRef,
    ProjectPortfolioLinkInput,
)

PageParam = Annotated[
    int,
    Field(
        description="Page number to return, default is 1",
        ge=1,
    ),
]

PageOrAllParam = Annotated[
    int | None,
    Field(
        description="Page number to return, default is None which means to retrieve all pages. "
        "Specify page number to retrieve a specific page when context limit is reached.",
        ge=1,
    ),
]

PerPageParam = Annotated[
    int,
    Field(
        description="The number of items per page. May be decreased if results exceed context window. "
        "If there is a change in per_page argument - retrieval must be started over with page = 1, "
        "as the paging could have changed.",
        ge=1,
    ),
]

CursorPerPageParam = Annotated[
    int,
    Field(
        description="The number of items per page for cursor-paginated endpoints. "
        "May be decreased if results exceed the context window.",
        ge=1,
    ),
]

IssueID = Annotated[
    str,
    Field(description="Issue ID in the format '<project>-<id>', like 'SOMEPROJECT-1'"),
]

QueueID = Annotated[
    str,
    Field(
        description="Queue (Project ID) to search in, like 'SOMEPROJECT'",
    ),
]

QueueIDFilter = Annotated[
    str | None,
    Field(
        description="Optional queue (Project ID) to scope the result to, like 'SOMEPROJECT'. "
        "Templates that are not bound to any queue are usable everywhere and are returned as well.",
    ),
]

IssueTemplateID = Annotated[
    str,
    Field(
        description="Issue template identifier, as returned by the `issue_templates_get_all` tool",
    ),
]

CommentTemplateID = Annotated[
    str,
    Field(
        description="Comment template identifier, as returned by the `comment_templates_get_all` tool",
    ),
]

# Write parameters shared by issue_create and issue_update. The update tool
# replaces list-valued fields instead of adding to them, so its variants append
# that clause to the same base description rather than restating it.
MarkupTypeParam = Annotated[
    str,
    Field(
        description="Markup type for description text. Use 'md' for YFM (markdown) markup."
    ),
]

_PARENT_DESCRIPTION = (
    "Parent issue reference. Object with 'id' (parent issue ID) "
    "and/or 'key' (parent issue key like 'QUEUE-123'); when both are given Tracker "
    "resolves by 'id'"
)

IssueParentParam = Annotated[
    IssueParentRef | str | None,
    Field(description=f"{_PARENT_DESCRIPTION}, or the bare key."),
]

IssueSprintParam = Annotated[
    list[IssueSprintRef] | None,
    Field(
        description="Sprint assignments. Array of objects, each with 'id' field "
        "containing the sprint ID (integer)."
    ),
]

IssueProjectParam = Annotated[
    IssueProjectRef | None,
    Field(
        description="Project assignment. Object with 'primary' (int, main project shortId) "
        "and optional 'secondary' (list of ints, additional project shortIds)."
    ),
]

IssueTagsParam = Annotated[
    list[str] | None,
    Field(description="Issue tags as array of strings."),
]

_FOLLOWERS_DESCRIPTION = (
    "Issue followers/watchers. Array of objects, each with an 'id' field "
    "holding the user ID (uid) or login."
)

IssueFollowersParam = Annotated[
    list[IssueFollowerRef] | None,
    Field(description=_FOLLOWERS_DESCRIPTION),
]

IssueFollowersUpdateParam = Annotated[
    list[IssueFollowerRef] | None,
    Field(description=f"{_FOLLOWERS_DESCRIPTION} Replaces the current follower list."),
]

_COMPONENTS_DESCRIPTION = (
    "Queue components. Array of objects with either 'id' (numeric component ID, "
    "from queue_get_metadata with expand=['components']) or 'name' (component name). "
    "Tracker resolves numbers as IDs and strings as names, so the object form is required "
    "to avoid a 422 on a numeric-looking name."
)

IssueComponentsParam = Annotated[
    list[IssueComponentRef] | None,
    Field(description=_COMPONENTS_DESCRIPTION),
]

IssueComponentsUpdateParam = Annotated[
    list[IssueComponentRef] | None,
    Field(
        description=f"{_COMPONENTS_DESCRIPTION} Replaces the current component list."
    ),
]

IssueIDs = Annotated[
    list[str],
    Field(
        description="Multiple Issue IDs. Each issue id is in the format '<project>-<id>', like 'SOMEPROJECT-1'"
    ),
]

UserID = Annotated[
    str,
    Field(
        description="User identifier - can be user login (e.g., 'john.doe') or user UID (e.g., '12345')"
    ),
]

EntityID = Annotated[
    str,
    Field(
        description="Entity identifier (id or shortId) of a Yandex Tracker project, portfolio or goal"
    ),
]


def entity_fields_description(default_fields: list[str]) -> str:
    """Shared wording for per-entity `fields` params (project/portfolio/goal).

    Kept as a function (not a constant) so each entity tool can plug in its
    own default field list while using identical phrasing everywhere.
    """
    return (
        "Entity fields to include in the response, selected from the allowed enum values. "
        "In order to not pollute the context window - select only the fields you actually need. "
        f"Not specifying this returns a reasonable default subset: {default_fields}. "
        "Custom (organization-defined) attributes are not supported by this tool."
    )


ProjectFieldsParam = Annotated[
    list[ProjectFieldsEnum] | None,
    Field(description=entity_fields_description(DEFAULT_ENTITY_FIELDS["project"])),
]

PortfolioFieldsParam = Annotated[
    list[PortfolioFieldsEnum] | None,
    Field(description=entity_fields_description(DEFAULT_ENTITY_FIELDS["portfolio"])),
]

GoalFieldsParam = Annotated[
    list[GoalFieldsEnum] | None,
    Field(description=entity_fields_description(DEFAULT_ENTITY_FIELDS["goal"])),
]


EntityInputParam = Annotated[
    str | None,
    Field(description="Substring to search for in the entity name (summary)"),
]


def entity_filter_description(status_values: tuple[str, ...]) -> str:
    """Shared wording for per-entity `filter` params (project/portfolio/goal).

    Takes the entity type's own `entityStatus` literal values so the description
    can enumerate the actually-valid values instead of a generic example.
    """
    return (
        "Exact-match field criteria to filter entities by, e.g. {'entityStatus': 'in_progress'}. "
        f"Valid 'entityStatus' values for this entity type: {', '.join(status_values)}. "
        "Other common keys: 'tags', 'lead', 'author'. A value may be a single string or a list of "
        "strings (matches any of them). Omitting this returns all entities, unfiltered."
    )


EntityFilterParam = Annotated[
    dict[str, str | list[str]] | None,
    Field(description=entity_filter_description(get_args(ProjectPortfolioStatus))),
]

GoalFilterParam = Annotated[
    dict[str, str | list[str]] | None,
    Field(description=entity_filter_description(get_args(GoalStatus))),
]

EntityOrderByParam = Annotated[
    str | None,
    Field(description="Field to sort results by"),
]

EntityOrderAscParam = Annotated[
    bool | None,
    Field(description="Sort order: True for ascending, False for descending"),
]

EntityRootOnlyParam = Annotated[
    bool | None,
    Field(
        description="When True, only return entities that are not nested under a parent entity"
    ),
]

EntitySummaryParam = Annotated[
    str | None,
    Field(description="Entity name/title"),
]

EntitySummaryRequiredParam = Annotated[
    str,
    Field(description="Entity name/title (required)"),
]

ProjectPortfolioStatusParam = Annotated[
    ProjectPortfolioStatus | None,
    Field(
        description=f"Entity status. One of: {', '.join(get_args(ProjectPortfolioStatus))}. "
        "Omitting this leaves the status unset/unchanged."
    ),
]

GoalStatusParam = Annotated[
    GoalStatus | None,
    Field(
        description=f"Goal status. One of: {', '.join(get_args(GoalStatus))}. "
        "Omitting this leaves the status unset/unchanged."
    ),
]

EntityDescriptionParam = Annotated[
    str | None,
    Field(description="Entity description"),
]

EntityLeadParam = Annotated[
    str | None,
    Field(description="User ID or login of the entity lead"),
]

EntityTeamUsersParam = Annotated[
    list[str] | None,
    Field(description="User IDs or logins of team members"),
]

EntityClientsParam = Annotated[
    list[str] | None,
    Field(description="User IDs or logins of customers"),
]

EntityFollowersParam = Annotated[
    list[str] | None,
    Field(description="User IDs or logins of followers"),
]

EntityStartParam = Annotated[
    datetime.date | datetime.datetime | None,
    Field(description="Start date or date/time"),
]

EntityEndParam = Annotated[
    datetime.date | datetime.datetime | None,
    Field(description="Deadline date or date/time"),
]

EntityTagsParam = Annotated[
    list[str] | None,
    Field(description="Tags"),
]

EntityParentEntityParam = Annotated[
    EntityParentEntityInput | None,
    Field(
        description="Containment: for a project/portfolio, the portfolio(s) it belongs to "
        "('Included in portfolio'); for a goal, its parent goal. "
        "`primary` is the main container id, `secondary` is additional portfolio ids "
        "(projects/portfolios only). "
        "Example: {'primary': 'portfolio_id_1', 'secondary': ['portfolio_id_2']}."
    ),
]

_LINKS_DESCRIPTION = (
    "Links from this entity to other entities (dependency/support relationships, not "
    "containment - use parent_entity for 'included in portfolio' or 'parent goal'). "
    "Each item is {{'relationship': ..., 'entity': <id of the other entity>}}. "
    "Valid relationship values: {relationships}. "
    "Example: [{{'relationship': '{example_relationship}', 'entity': '<other entity id>'}}]. "
    "On update this REPLACES the entity's existing links, so pass the full desired set."
)

ProjectPortfolioLinksParam = Annotated[
    list[ProjectPortfolioLinkInput] | None,
    Field(
        description=_LINKS_DESCRIPTION.format(
            relationships=", ".join(
                f"'{value}'" for value in get_args(ProjectPortfolioLinkRelationship)
            ),
            example_relationship=get_args(ProjectPortfolioLinkRelationship)[0],
        )
    ),
]

GoalLinksParam = Annotated[
    list[GoalLinkInput] | None,
    Field(
        description=_LINKS_DESCRIPTION.format(
            relationships=", ".join(
                f"'{value}'" for value in get_args(GoalLinkRelationship)
            ),
            example_relationship=get_args(GoalLinkRelationship)[0],
        )
    ),
]

EntityCommentParam = Annotated[
    str | None,
    Field(description="Optional comment describing the update"),
]

EntityVersionParam = Annotated[
    int | None,
    Field(
        description="Expected current version of the entity, for optimistic concurrency control. "
        "If provided and stale, the update is rejected."
    ),
]

EntityWithBoardParam = Annotated[
    bool,
    Field(description="Whether to also delete the board associated with the entity"),
]

EntityTeamAccessParam = Annotated[
    bool | None,
    Field(description="Whether access is limited to entity participants"),
]


EntityCommentIDParam = Annotated[
    int,
    Field(
        description="Comment ID (integer), as returned in the `id` field by "
        "*_get_comments or *_add_comment, e.g. 12345."
    ),
]

EntityCommentTextParam = Annotated[
    str,
    Field(
        description="Comment text (Markdown/YFM supported). "
        "Example: 'Looks good, approving the plan.'"
    ),
]

EntityCommentSummoneesParam = Annotated[
    list[str] | None,
    Field(
        description="Optional list of user logins or IDs to summon into the discussion "
        "so they get notified. Example: ['i.ivanov', 'j.doe']. "
        "IMPORTANT: do NOT rely on '@login' inside the comment text for this — use this "
        "parameter instead."
    ),
]

EntityCommentMaillistSummoneesParam = Annotated[
    list[str] | None,
    Field(
        description="Optional list of mailing list emails to summon. "
        "Example: ['team@example.com']."
    ),
]


YTQuery = Annotated[
    str,
    Field(
        description=(
            """Search query to filter issues using Yandex Tracker Query.\n"""
            """# General instructions\n"""
            """1. To search by a specific field use the following syntax: `Description: "some issue description"`\n"""
            """2. Multiple fields should be separated by space: `Description: "some issue description" Created: today()`\n"""
            """3. If you need to specify multiple values for the same field - provide them using comma (,), e.g.: `author: "vpupkin","iivanov"`\n"""
            """4. You may specify multiple conditions and combine them using `AND` and `OR` statements, e.g. `<param_1>: "<value_1>" AND <param_2>: "<value_2>"`\n"""
            """5. You may use brackets for complex logical expressions\n"""
            """6. To find issues with exact string matching in the field use this syntax: `Summary: #"Version 2.0"`. If you need to pass special characters - you must escape them using `\\` symbol\n"""
            """7. To find issues that don't contain the specified text use this syntax: `Summary: !"Version 2.0"`. If you need to pass special characters - you must escape them using `\\` symbol\n"""
            """8. If you need to search by local queue field use the following syntax: `<QUEUE>.<LOCAL_FIELD_KEY>: "<value>", where <QUEUE> is a queue key, <LOCAL_FIELD_KEY> is a local field's key from the `queue_get_local_fields` tool result.\n"""
            """9. For dates use the format YYYY-MM-DD.\n"""
            """10. For numerical values you may use comparison operators (>, <, >=, <=): `<param>: ><value>`.\n"""
            """11. To sort the result specify the `Sort By` directive (you may provide ASC or DESC for the sort order): `"Sort By": Created ASC`.\n"""
            """12. For Assignee field and any other field representing a user (such as Author and others) always use username and not name.\n"""
            """# Functions\n"""
            """These functions may be used, for example: `Created: week()` - return issues created on the current week"\n"""
            """* `empty()` - empty value\n"""
            """* `notEmpty()` - not empty value\n"""
            """* `now()` - current time\n"""
            """* `today()` - current date\n"""
            """* `week()` - current week\n"""
            """* `month()` - current month\n"""
            """* `quarter()` - current quarter\n"""
            """* `year()` - current year\n"""
            """* `unresolved()` - there is no resolution\n"""
            """* `me()` - currently logged in user\n"""
            """# Examples\n"""
            """Find issues in a specific queue: `"Queue": "PROJ"`\n"""
            """Find issues by an assignee: `"Assignee": "i.ivanov"`\n"""
            """Find not resolved (open, in progress) issues: `"Resolution": unresolved()`\n"""
            """Find issues in specific status: `"Status": "Открыт", "В работе"`\n"""
            """Find issues created in a specific range: `"Created": "2017-01-01".."2017-01-30"`\n"""
            """Find issues created by currently logged in user: `"Author": me()"`\n"""
            """Find issues assigned to currently logged in user: `"Assignee": me()"`\n"""
            """Find issues created no earlier than 1 week and 1 day before today: `Created: > today() - "1w 1d"`\n"""
            """Complete instructions page is available here: https://yandex.ru/support/tracker/ru/user/query-filter\n"""
        )
    ),
]

instructions = """Tools for interacting with Yandex Tracker issue tracking system.
Use these tools to:
- Search and browse queues and issues
- Search and manage projects, portfolios, and goals (project-management entities, distinct from queues)
- View issue details, comments, attachments, and worklogs
- Get information about users, statuses, and issue types
- Query issues using Yandex Query Language (YQL)

In russian Yandex Tracker is called "Яндекс Трекер", "Трекер".
Queues may be called "Очереди".
Tasks may be called "Задачи", "Issues", "Таски", "ишью".
Projects may be called "Проекты".
Portfolios may be called "Портфели".
Goals may be called "Цели".

## Queues vs. projects/portfolios/goals

A "queue" (e.g. `SOMEPROJECT` in an issue key like `SOMEPROJECT-1`) is where issues live and get
numbered - use `queues_get_all`, `issues_find`, etc. A "project"/"portfolio"/"goal" (`project_*`,
`portfolio_*`, `goal_*` tools) is a separate project-management entity used to group and track
progress across issues from possibly many queues. Don't confuse a queue key with an entity id: entity
ids come from `project_find`/`portfolio_find`/`goal_find`/`*_get` results, not from issue keys.

## Linking issues, projects, portfolios, and goals together

- Issue -> project: set the issue's `project` field (on `issue_create`/`issue_update`) to
  `{"primary": <project shortId>, "secondary": [<other project shortIds>]}`. The project's `shortId`
  comes from `project_get`/`project_find`. There is no direct issue-to-portfolio or issue-to-goal link;
  portfolios/goals track progress via the projects (and, for goals, other goals) linked into them.
- Project/portfolio -> portfolio (containment, "included in portfolio"): set `parent_entity` on
  `project_create`/`project_update`/`portfolio_create`/`portfolio_update` to
  `{"primary": <portfolio id>, "secondary": [<other portfolio ids>]}`.
- Goal -> parent goal (containment): set `parent_entity.primary` on `goal_create`/`goal_update` to the
  parent goal's id.
- Cross-entity relationships that aren't containment (e.g. a project "depends on" another project, or
  "works towards" a goal): use the `links` param on `project_create`/`portfolio_create`/`goal_create`/
  `*_update`, e.g. `[{"relationship": "works towards", "entity": <goal id>}]`. `links` REPLACES the
  entity's full link set on update, so re-send existing links you want to keep alongside new ones -
  fetch them first with `*_get(fields=["links"])` if unsure what's already there.

When using tools that accept `page` and/or `per_page` parameters and when the task is to find something in the result set (or to receive all available data) - always call the tool as many times as needed increasing the `page` parameter until the result set is exhausted. If you stumble with the context size limit — try to change the `per_page` parameter to a lower value and restart the search from the `page=1`.

Some tools use cursor pagination instead of `page` (e.g. `issue_get_changelog`): they accept a `cursor` argument and return a `next_cursor` value. To get all data, keep calling the tool passing the previous `next_cursor` as `cursor` until `next_cursor` is null. Do not change `per_page` mid-pagination; if you must, restart with `cursor` empty.
"""
