"""User-related MCP tools (read-only)."""

from typing import Annotated, Any

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from thefuzz import process

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.errors import TrackerError
from mcp_tracker.mcp.params import PageParam, PerPageParam, UserID
from mcp_tracker.mcp.utils import get_yandex_auth
from mcp_tracker.settings import Settings
from mcp_tracker.tracker.proto.types.users import User


def register_user_tools(_settings: Settings, mcp: FastMCP[Any]) -> None:
    """Register user-related tools (all read-only)."""

    @mcp.tool(
        title="Get All Users",
        description="Get information about user accounts registered in the organization",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def users_get_all(
        ctx: Context[Any, AppContext],
        page: PageParam = 1,
        per_page: PerPageParam = 50,
    ) -> list[User]:
        return await ctx.request_context.lifespan_context.users.users_list(
            per_page=per_page,
            page=page,
            auth=get_yandex_auth(ctx),
        )

    @mcp.tool(
        title="Search Users",
        description="Search user based on login, email or real name (first or last name, or both). "
        "Returns either single user or multiple users if several match the query or an empty list "
        "if no users matched.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def users_search(
        ctx: Context[Any, AppContext],
        login_or_email_or_name: Annotated[
            str, Field(description="User login, email or real name to search for")
        ],
    ) -> list[User]:
        per_page = 100
        page = 1

        login_or_email_or_name = login_or_email_or_name.strip().lower()

        all_users: list[User] = []

        while True:
            batch = await ctx.request_context.lifespan_context.users.users_list(
                per_page=per_page,
                page=page,
                auth=get_yandex_auth(ctx),
            )

            if not batch:
                break

            for user in batch:
                if user.login and login_or_email_or_name == user.login.strip().lower():
                    return [user]

                if user.email and login_or_email_or_name == user.email.strip().lower():
                    return [user]

            all_users.extend(batch)
            page += 1

        names = {
            idx: f"{u.first_name} {u.last_name}" for idx, u in enumerate(all_users)
        }
        results = process.extractBests(
            login_or_email_or_name, names, score_cutoff=80, limit=3
        )
        matched_users = [all_users[idx] for name, score, idx in results]
        return matched_users

    @mcp.tool(
        title="Get User",
        description="Get information about a specific user by login or UID",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def user_get(
        ctx: Context[Any, AppContext],
        user_id: UserID,
    ) -> User:
        user = await ctx.request_context.lifespan_context.users.user_get(
            user_id,
            auth=get_yandex_auth(ctx),
        )
        if user is None:
            raise TrackerError(f"User `{user_id}` not found.")

        return user

    @mcp.tool(
        title="Get Current User",
        description="Get information about the current authenticated user",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def user_get_current(
        ctx: Context[Any, AppContext],
    ) -> User:
        return await ctx.request_context.lifespan_context.users.user_get_current(
            auth=get_yandex_auth(ctx),
        )
