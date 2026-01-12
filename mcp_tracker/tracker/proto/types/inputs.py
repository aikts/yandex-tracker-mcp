from pydantic import BaseModel, Field


class IssueUpdateParent(BaseModel):
    """Parent issue reference for issue update."""

    id: str | None = Field(None, description="Parent issue ID")
    key: str | None = Field(None, description="Parent issue key (e.g., 'QUEUE-123')")


class IssueUpdateSprint(BaseModel):
    """Sprint reference for issue update."""

    id: int = Field(..., description="Sprint ID")


class IssueUpdateType(BaseModel):
    """Issue type reference for issue update."""

    id: str | None = Field(None, description="Issue type ID")
    key: str | None = Field(None, description="Issue type key (e.g., 'bug', 'task')")


class IssueUpdatePriority(BaseModel):
    """Priority reference for issue update."""

    id: str | None = Field(None, description="Priority ID")
    key: str | None = Field(
        None, description="Priority key (e.g., 'critical', 'normal')"
    )


class IssueUpdateFollower(BaseModel):
    """Follower reference for issue update."""

    id: str = Field(..., description="User ID or login")


class IssueUpdateProject(BaseModel):
    """Project configuration for issue update."""

    primary: int | None = Field(
        None, description="Primary project ID (shortId of the project)"
    )
    secondary: list[int] | None = Field(
        None, description="Secondary project IDs (shortId of additional projects)"
    )
