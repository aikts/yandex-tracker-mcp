from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.entities import GoalEntity, GoalSearchResult
from mcp_tracker.tracker.proto.types.issues import CommentsPage, IssueComment
from tests.mcp.conftest import get_tool_result_content


class TestGoalGet:
    async def test_returns_goal(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goal: GoalEntity,
    ) -> None:
        mock_entities_protocol.goal_get.return_value = sample_goal

        result = await client_session.call_tool("goal_get", {"entity_id": "ghi789"})

        assert not result.isError
        mock_entities_protocol.goal_get.assert_called_once()
        content = get_tool_result_content(result)
        assert content["id"] == sample_goal.id
        assert sample_goal.fields is not None
        assert content["fields"]["summary"] == sample_goal.fields.summary

    async def test_passes_entity_id_and_fields(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goal: GoalEntity,
    ) -> None:
        mock_entities_protocol.goal_get.return_value = sample_goal

        await client_session.call_tool(
            "goal_get",
            {"entity_id": "ghi789", "fields": ["summary", "entityStatus"]},
        )

        mock_entities_protocol.goal_get.assert_called_once_with(
            "ghi789", fields=["summary", "entityStatus"], auth=YandexAuth()
        )

    async def test_omitted_fields_passed_as_none(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goal: GoalEntity,
    ) -> None:
        mock_entities_protocol.goal_get.return_value = sample_goal

        await client_session.call_tool("goal_get", {"entity_id": "ghi789"})

        call_kwargs = mock_entities_protocol.goal_get.call_args.kwargs
        assert call_kwargs["fields"] is None


class TestGoalFind:
    async def test_returns_goals(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goals: GoalSearchResult,
    ) -> None:
        mock_entities_protocol.goal_find.return_value = sample_goals

        result = await client_session.call_tool("goal_find", {})

        assert not result.isError
        mock_entities_protocol.goal_find.assert_called_once()
        content = get_tool_result_content(result)
        assert content["hits"] == sample_goals.hits
        assert len(content["values"]) == len(sample_goals.values)

    async def test_passes_search_parameters(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goals: GoalSearchResult,
    ) -> None:
        mock_entities_protocol.goal_find.return_value = sample_goals

        await client_session.call_tool(
            "goal_find",
            {
                "input": "revenue",
                "filter": {"entityStatus": "according_to_plan"},
                "order_by": "end",
                "order_asc": True,
                "root_only": False,
                "page": 1,
                "per_page": 20,
            },
        )

        mock_entities_protocol.goal_find.assert_called_once_with(
            input="revenue",
            filter={"entityStatus": "according_to_plan"},
            order_by="end",
            order_asc=True,
            root_only=False,
            per_page=20,
            page=1,
            fields=None,
            auth=YandexAuth(),
        )

    async def test_optional_parameters_omitted(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_goals: GoalSearchResult,
    ) -> None:
        mock_entities_protocol.goal_find.return_value = sample_goals

        await client_session.call_tool("goal_find", {})

        call_kwargs = mock_entities_protocol.goal_find.call_args.kwargs
        assert call_kwargs["input"] is None
        assert call_kwargs["filter"] is None
        assert call_kwargs["order_by"] is None
        assert call_kwargs["order_asc"] is None
        assert call_kwargs["root_only"] is None


class TestGoalGetComments:
    async def test_returns_comments(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_entities_protocol.goal_get_comments.return_value = CommentsPage(
            comments=sample_comments, next_cursor="99"
        )

        result = await client_session.call_tool(
            "goal_get_comments", {"entity_id": "ghi789"}
        )

        assert not result.isError
        mock_entities_protocol.goal_get_comments.assert_called_once_with(
            "ghi789", per_page=50, cursor=None, auth=YandexAuth()
        )
        content = get_tool_result_content(result)
        assert content["next_cursor"] == "99"
        assert len(content["comments"]) == len(sample_comments)
        assert content["comments"][0]["text"] == sample_comments[0].text

    async def test_passes_pagination_params(
        self,
        client_session: ClientSession,
        mock_entities_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_entities_protocol.goal_get_comments.return_value = CommentsPage(
            comments=sample_comments
        )

        result = await client_session.call_tool(
            "goal_get_comments",
            {"entity_id": "ghi789", "per_page": 10, "cursor": "42"},
        )

        assert not result.isError
        mock_entities_protocol.goal_get_comments.assert_called_once_with(
            "ghi789", per_page=10, cursor="42", auth=YandexAuth()
        )
        assert get_tool_result_content(result)["next_cursor"] is None
