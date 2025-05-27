from typing import Annotated

from pydantic import Field

IssueID = Annotated[
    str,
    Field(description="Issue ID in the format '<project>-<id>', like 'SOMEPROJECT-1'"),
]

IssueIDs = Annotated[
    list[str],
    Field(
        description="Multiple Issue IDs. Each issue id is in the format '<project>-<id>', like 'SOMEPROJECT-1'"
    ),
]
