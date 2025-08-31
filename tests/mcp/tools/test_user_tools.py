from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.tracker.proto.types.users import User
from tests.mcp.conftest import get_tool_result_content


class TestUsersGetAll:
    async def test_returns_users(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.return_value = sample_users

        result = await client_session.call_tool("users_get_all", {})

        assert not result.isError
        mock_users_protocol.users_list.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_users)
        assert content[0]["login"] == sample_users[0].login
        assert content[0]["display"] == sample_users[0].display

    async def test_with_pagination(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.return_value = sample_users

        result = await client_session.call_tool(
            "users_get_all", {"page": 2, "per_page": 25}
        )

        assert not result.isError
        call_kwargs = mock_users_protocol.users_list.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["per_page"] == 25
        content = get_tool_result_content(result)
        assert len(content) == len(sample_users)


class TestUsersSearch:
    async def test_finds_user_by_exact_login(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.side_effect = [sample_users, []]

        result = await client_session.call_tool(
            "users_search", {"login_or_email_or_name": "testuser"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["login"] == "testuser"

    async def test_finds_user_by_exact_email(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.side_effect = [sample_users, []]

        result = await client_session.call_tool(
            "users_search", {"login_or_email_or_name": "testuser@example.com"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["email"] == "testuser@example.com"

    async def test_fuzzy_matches_by_name(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_users: list[User],
    ) -> None:
        mock_users_protocol.users_list.side_effect = [sample_users, []]

        result = await client_session.call_tool(
            "users_search", {"login_or_email_or_name": "Test User"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        # Should find at least one user matching "Test User"
        assert len(content) >= 1

    async def test_returns_empty_list_when_no_match(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
    ) -> None:
        mock_users_protocol.users_list.side_effect = [[], []]

        result = await client_session.call_tool(
            "users_search", {"login_or_email_or_name": "nonexistent"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == 0


class TestUserGet:
    async def test_returns_user(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_user: User,
    ) -> None:
        mock_users_protocol.user_get.return_value = sample_user

        result = await client_session.call_tool("user_get", {"user_id": "testuser"})

        assert not result.isError
        mock_users_protocol.user_get.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["login"] == sample_user.login
        assert content["display"] == sample_user.display
        assert content["email"] == sample_user.email

    async def test_user_not_found_raises_error(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
    ) -> None:
        mock_users_protocol.user_get.return_value = None

        result = await client_session.call_tool("user_get", {"user_id": "nonexistent"})

        assert result.isError


class TestUserGetCurrent:
    async def test_returns_current_user(
        self,
        client_session: ClientSession,
        mock_users_protocol: AsyncMock,
        sample_user: User,
    ) -> None:
        mock_users_protocol.user_get_current.return_value = sample_user

        result = await client_session.call_tool("user_get_current", {})

        assert not result.isError
        mock_users_protocol.user_get_current.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["login"] == sample_user.login
        assert content["display"] == sample_user.display
