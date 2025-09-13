from typing import Annotated

from pydantic import Field

PageParam = Annotated[
    int,
    Field(
        description="Page number to return, default is 1",
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
- Search and browse projects (queues) and issues
- View issue details, comments, attachments, and worklogs
- Get information about users, statuses, and issue types
- Query issues using Yandex Query Language (YQL)

In russian Yandex Tracker is called "Яндекс Трекер", "Трекер".
Queues may be called "Очереди".
Tasks may be called "Задачи", "Issues", "Таски", "ишью".

When using tools that accept `page` and/or `per_page` parameters and when the task is to find something in the result set (or to receive all available data) - always call the tool as many times as needed increasing the `page` parameter until ther result set is exhausted. If you stumble with the context size limit — try to change the `per_page` parameter to a lower value and restart the search from the `page=1`.
"""
