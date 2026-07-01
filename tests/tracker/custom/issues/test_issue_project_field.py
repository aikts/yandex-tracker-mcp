from mcp_tracker.tracker.proto.types.issues import Issue, IssueFieldsEnum


class TestIssueProjectField:
    def test_project_in_fields_enum(self) -> None:
        # `project` must be selectable in issues_find `fields`.
        assert "project" in IssueFieldsEnum.__members__

    def test_issue_parses_project(self) -> None:
        issue = Issue.model_validate(
            {
                "key": "TEST-1",
                "project": {"primary": {"id": "p-1", "display": "Proj"}},
            }
        )
        assert issue.project is not None
        assert issue.project["primary"]["id"] == "p-1"
