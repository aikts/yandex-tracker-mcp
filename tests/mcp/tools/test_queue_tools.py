from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.fields import GlobalField, LocalField
from mcp_tracker.tracker.proto.types.queues import Queue, QueueVersion
from tests.mcp.conftest import get_tool_result_content


class TestQueuesGetAll:
    async def test_returns_all_queues(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queues: list[Queue],
    ) -> None:
        # First call returns queues, second call returns empty list to stop pagination
        mock_queues_protocol.queues_list.side_effect = [sample_queues, []]

        result = await client_session.call_tool("queues_get_all", {})

        assert not result.isError
        mock_queues_protocol.queues_list.assert_called()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_queues)
        assert content[0]["key"] == sample_queues[0].key
        assert content[0]["name"] == sample_queues[0].name

    async def test_with_specific_page(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queues: list[Queue],
    ) -> None:
        mock_queues_protocol.queues_list.return_value = sample_queues

        result = await client_session.call_tool(
            "queues_get_all", {"page": 2, "per_page": 50}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_queues)

    async def test_respects_queue_limits(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queues: list[Queue],
    ) -> None:
        # Include an ALLOWED queue in the response
        sample_queues[0].key = "ALLOWED"
        mock_queues_protocol.queues_list.side_effect = [sample_queues, []]

        result = await client_session_with_limits.call_tool("queues_get_all", {})

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        # Only the ALLOWED queue should be returned
        assert all(q["key"] == "ALLOWED" for q in content)


class TestQueueGetTags:
    async def test_returns_tags(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queue_tags: list[str],
    ) -> None:
        mock_queues_protocol.queues_get_tags.return_value = sample_queue_tags

        result = await client_session.call_tool("queue_get_tags", {"queue_id": "TEST"})

        assert not result.isError
        mock_queues_protocol.queues_get_tags.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert content == sample_queue_tags

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "queue_get_tags", {"queue_id": "RESTRICTED"}
        )

        assert result.isError
        mock_queues_protocol.queues_get_tags.assert_not_called()


class TestQueueGetVersions:
    async def test_returns_versions(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queue_versions: list[QueueVersion],
    ) -> None:
        mock_queues_protocol.queues_get_versions.return_value = sample_queue_versions

        result = await client_session.call_tool(
            "queue_get_versions", {"queue_id": "TEST"}
        )

        assert not result.isError
        mock_queues_protocol.queues_get_versions.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_queue_versions)
        assert content[0]["name"] == sample_queue_versions[0].name

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "queue_get_versions", {"queue_id": "RESTRICTED"}
        )

        assert result.isError
        mock_queues_protocol.queues_get_versions.assert_not_called()


class TestQueueGetFields:
    async def test_returns_global_and_local_fields(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_global_fields: list[GlobalField],
        sample_local_fields: list[LocalField],
    ) -> None:
        mock_queues_protocol.queues_get_fields.return_value = sample_global_fields
        mock_queues_protocol.queues_get_local_fields.return_value = sample_local_fields

        result = await client_session.call_tool(
            "queue_get_fields", {"queue_id": "TEST", "include_local_fields": True}
        )

        assert not result.isError
        mock_queues_protocol.queues_get_fields.assert_called_once()
        mock_queues_protocol.queues_get_local_fields.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        # Should contain both global and local fields
        expected_count = len(sample_global_fields) + len(sample_local_fields)
        assert len(content) == expected_count

    async def test_global_fields_only(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_global_fields: list[GlobalField],
    ) -> None:
        mock_queues_protocol.queues_get_fields.return_value = sample_global_fields

        result = await client_session.call_tool(
            "queue_get_fields", {"queue_id": "TEST", "include_local_fields": False}
        )

        assert not result.isError
        mock_queues_protocol.queues_get_fields.assert_called_once()
        mock_queues_protocol.queues_get_local_fields.assert_not_called()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_global_fields)
        assert content[0]["id"] == sample_global_fields[0].id

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "queue_get_fields", {"queue_id": "RESTRICTED"}
        )

        assert result.isError
        mock_queues_protocol.queues_get_fields.assert_not_called()


class TestQueueGetMetadata:
    async def test_returns_metadata(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queue: Queue,
    ) -> None:
        mock_queues_protocol.queue_get.return_value = sample_queue

        result = await client_session.call_tool(
            "queue_get_metadata", {"queue_id": "TEST"}
        )

        assert not result.isError
        mock_queues_protocol.queue_get.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["key"] == sample_queue.key
        assert content["name"] == sample_queue.name

    async def test_with_expand_options(
        self,
        client_session: ClientSession,
        mock_queues_protocol: AsyncMock,
        sample_queue: Queue,
    ) -> None:
        mock_queues_protocol.queue_get.return_value = sample_queue

        result = await client_session.call_tool(
            "queue_get_metadata",
            {"queue_id": "TEST", "expand": ["issueTypesConfig", "workflows"]},
        )

        assert not result.isError
        mock_queues_protocol.queue_get.assert_called_once()
        # Verify expand options were passed
        call_kwargs = mock_queues_protocol.queue_get.call_args.kwargs
        assert "expand" in call_kwargs
        assert "issueTypesConfig" in call_kwargs["expand"]
        content = get_tool_result_content(result)
        assert content["key"] == sample_queue.key

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_queues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "queue_get_metadata", {"queue_id": "RESTRICTED"}
        )

        assert result.isError
        mock_queues_protocol.queue_get.assert_not_called()
