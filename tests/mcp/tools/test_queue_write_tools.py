from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.queues import QueueVersion
from tests.mcp.conftest import get_tool_result_content


class TestQueueCreateVersion:
    async def test_creates_version(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queue_versions: list[QueueVersion],
    ) -> None:
        created_version = sample_queue_versions[0]
        mock_queues_protocol.queue_create_version.return_value = created_version

        result = await client_session.call_tool(
            "queue_create_version",
            {
                "queue_id": "TEST",
                "name": "1.0.0",
                "description": "Initial release",
                "start_date": "2023-01-01",
                "due_date": "2023-12-31",
            },
        )

        assert not result.isError
        mock_queues_protocol.queue_create_version.assert_called_once()
        call_args = mock_queues_protocol.queue_create_version.call_args
        assert call_args.args[0] == "TEST"
        assert call_args.kwargs["name"] == "1.0.0"
        assert call_args.kwargs["description"] == "Initial release"
        assert call_args.kwargs["start_date"].isoformat() == "2023-01-01"
        assert call_args.kwargs["due_date"].isoformat() == "2023-12-31"

        content = get_tool_result_content(result)
        assert content["name"] == created_version.name

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "queue_create_version",
            {"queue_id": "RESTRICTED", "name": "1.0.0"},
        )

        assert result.isError
        mock_queues_protocol.queue_create_version.assert_not_called()
