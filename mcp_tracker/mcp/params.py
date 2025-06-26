from typing import Annotated

from pydantic import Field

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
