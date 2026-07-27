from mcp_tracker.tracker.proto.types.issues import IssueComment


def test_model_is_complete_after_import() -> None:
    assert IssueComment.__pydantic_complete__
