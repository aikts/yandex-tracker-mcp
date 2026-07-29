from mcp.client.session import ClientSession

from tests.mcp.conftest import get_tool_result_content


class TestIssueDeleteStub:
    async def test_returns_instructions(self, client_session: ClientSession) -> None:
        result = await client_session.call_tool("issue_delete", {"issue_id": "PL-28"})

        assert not result.isError
        text = get_tool_result_content(result)
        assert "PL-28" in text
        assert "queue_create" in text
        assert "issue_move" in text
        assert "queue_delete" in text

    async def test_registered_in_read_only(
        self, client_session_read_only: ClientSession
    ) -> None:
        # It's a read-only guiding stub, so it stays available in read-only mode.
        result = await client_session_read_only.call_tool(
            "issue_delete", {"issue_id": "PL-28"}
        )
        assert not result.isError
