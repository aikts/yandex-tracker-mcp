from pathlib import Path
from unittest.mock import AsyncMock

from mcp.client.session import ClientSession

from mcp_tracker.mcp.context import AppContext
from mcp_tracker.mcp.server import create_mcp_server
from mcp_tracker.tracker.custom.errors import AttachmentNotFound
from mcp_tracker.tracker.proto.common import YandexAuth
from mcp_tracker.tracker.proto.types.issues import (
    ChangelogComments,
    ChangelogEntry,
    ChangelogExecutedTrigger,
    ChangelogPage,
    ChangelogReference,
    ChecklistItem,
    CommentsPage,
    Issue,
    IssueAttachment,
    IssueComment,
    IssueLink,
    IssueTransition,
    Worklog,
)
from tests.mcp.conftest import (
    create_test_settings,
    get_tool_result_content,
    make_test_lifespan,
    page,
    safe_client_session,
)


class TestIssueGetUrl:
    async def test_returns_tracker_url(
        self,
        client_session: ClientSession,
    ) -> None:
        result = await client_session.call_tool(
            "issue_get_url", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content == "https://tracker.yandex.ru/TEST-123"


class TestIssueGet:
    async def test_returns_issue(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_get.return_value = sample_issue

        result = await client_session.call_tool("issue_get", {"issue_id": "TEST-123"})

        assert not result.isError
        mock_issues_protocol.issue_get.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["key"] == sample_issue.key
        assert content["summary"] == sample_issue.summary

    async def test_with_description_excluded(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issue: Issue,
    ) -> None:
        mock_issues_protocol.issue_get.return_value = sample_issue

        result = await client_session.call_tool(
            "issue_get", {"issue_id": "TEST-123", "include_description": False}
        )

        assert not result.isError
        mock_issues_protocol.issue_get.assert_called_once()
        content = get_tool_result_content(result)
        assert content["key"] == sample_issue.key
        # Description should be None when excluded
        assert content.get("description") is None

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_get", {"issue_id": "RESTRICTED-123"}
        )

        assert result.isError
        mock_issues_protocol.issue_get.assert_not_called()


class TestIssueGetComments:
    async def test_returns_comments(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_issues_protocol.issue_get_comments.return_value = CommentsPage(
            comments=sample_comments, next_cursor="99"
        )

        result = await client_session.call_tool(
            "issue_get_comments", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_comments.assert_called_once_with(
            "TEST-123", per_page=50, cursor=None, auth=YandexAuth()
        )
        content = get_tool_result_content(result)
        assert content["next_cursor"] == "99"
        assert len(content["comments"]) == len(sample_comments)
        assert content["comments"][0]["text"] == sample_comments[0].text

    async def test_passes_pagination_params(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_issues_protocol.issue_get_comments.return_value = CommentsPage(
            comments=sample_comments
        )

        result = await client_session.call_tool(
            "issue_get_comments",
            {"issue_id": "TEST-123", "per_page": 10, "cursor": "42"},
        )

        assert not result.isError
        mock_issues_protocol.issue_get_comments.assert_called_once_with(
            "TEST-123", per_page=10, cursor="42", auth=YandexAuth()
        )

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_get_comments", {"issue_id": "RESTRICTED-123"}
        )

        assert result.isError
        mock_issues_protocol.issue_get_comments.assert_not_called()

    async def test_fields_filters_response(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_comments: list[IssueComment],
    ) -> None:
        mock_issues_protocol.issue_get_comments.return_value = CommentsPage(
            comments=sample_comments
        )

        result = await client_session.call_tool(
            "issue_get_comments", {"issue_id": "TEST-123", "fields": ["text"]}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["comments"][0]["text"] == sample_comments[0].text
        assert content["comments"][0].get("createdBy") is None


class TestIssueGetLinks:
    async def test_returns_links(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_links: list[IssueLink],
    ) -> None:
        mock_issues_protocol.issues_get_links.return_value = sample_links

        result = await client_session.call_tool(
            "issue_get_links", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issues_get_links.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_links)
        assert content[0]["direction"] == sample_links[0].direction


class TestIssuesFind:
    async def test_finds_issues(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(
            sample_issues, hits=403, pages=5
        )

        result = await client_session.call_tool("issues_find", {"query": "Queue: TEST"})

        assert not result.isError
        mock_issues_protocol.issues_find.assert_called_once()
        content = get_tool_result_content(result)
        assert len(content["values"]) == len(sample_issues)
        assert content["values"][0]["key"] == sample_issues[0].key

    async def test_returns_pagination_totals(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(
            sample_issues, hits=403, pages=5
        )

        result = await client_session.call_tool("issues_find", {"query": "Queue: TEST"})

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["hits"] == 403
        assert content["pages"] == 5

    async def test_with_pagination(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(sample_issues)

        result = await client_session.call_tool(
            "issues_find", {"query": "Queue: TEST", "page": 2, "per_page": 50}
        )

        assert not result.isError
        call_kwargs = mock_issues_protocol.issues_find.call_args.kwargs
        assert call_kwargs["page"] == 2
        assert call_kwargs["per_page"] == 50
        content = get_tool_result_content(result)
        assert len(content["values"]) == len(sample_issues)

    async def test_excludes_description_by_default(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(sample_issues)

        result = await client_session.call_tool("issues_find", {"query": "Queue: TEST"})

        assert not result.isError
        mock_issues_protocol.issues_find.assert_called_once()
        content = get_tool_result_content(result)
        # By default, description is excluded (set to None)
        for issue in content["values"]:
            assert issue.get("description") is None

    async def test_fields_are_pushed_down_to_the_api(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(sample_issues)

        result = await client_session.call_tool(
            "issues_find", {"query": "Queue: TEST", "fields": ["key", "story_points"]}
        )

        assert not result.isError
        # The API only understands Tracker's own spelling of a field name.
        assert sorted(mock_issues_protocol.issues_find.call_args.kwargs["fields"]) == [
            "key",
            "storyPoints",
        ]

    async def test_fields_accept_trackers_own_spelling(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        issue = Issue.model_construct(key="TEST-123", story_points=3.0)
        mock_issues_protocol.issues_find.return_value = page([issue])

        result = await client_session.call_tool(
            "issues_find", {"query": "Queue: TEST", "fields": ["key", "storyPoints"]}
        )

        assert not result.isError
        assert mock_issues_protocol.issues_find.call_args.kwargs["fields"] == [
            "key",
            "storyPoints",
        ]
        # Requested Tracker's way, kept under the model's own name.
        content = get_tool_result_content(result)
        assert content["values"][0]["storyPoints"] == 3.0

    async def test_both_spellings_of_one_field_are_sent_once(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(sample_issues)

        result = await client_session.call_tool(
            "issues_find",
            {"query": "Queue: TEST", "fields": ["story_points", "storyPoints"]},
        )

        assert not result.isError
        assert mock_issues_protocol.issues_find.call_args.kwargs["fields"] == [
            "storyPoints"
        ]

    async def test_fields_accept_a_field_the_model_does_not_declare(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        """A queue's local fields and the standard fields `Issue` omits are only
        reachable because the selector is free-form."""
        issue = Issue.model_validate(
            {
                "key": "TEST-123",
                "resolution": {"id": "1", "key": "fixed"},
                "694c13a2974fc069fc7db927--chapter": "Support",
                "queue": {"id": "1", "key": "TEST"},
            }
        )
        mock_issues_protocol.issues_find.return_value = page([issue])

        result = await client_session.call_tool(
            "issues_find",
            {
                "query": "Queue: TEST",
                "fields": ["key", "resolution", "694c13a2974fc069fc7db927--chapter"],
            },
        )

        assert not result.isError
        assert mock_issues_protocol.issues_find.call_args.kwargs["fields"] == [
            "key",
            "resolution",
            "694c13a2974fc069fc7db927--chapter",
        ]
        content = get_tool_result_content(result)
        # Requested extras survive; `queue`, which was not asked for, does not.
        assert content["values"][0] == {
            "key": "TEST-123",
            "resolution": {"id": "1", "key": "fixed"},
            "694c13a2974fc069fc7db927--chapter": "Support",
        }

    async def test_no_fields_param_when_not_selected(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_issues: list[Issue],
    ) -> None:
        mock_issues_protocol.issues_find.return_value = page(sample_issues)

        result = await client_session.call_tool("issues_find", {"query": "Queue: TEST"})

        assert not result.isError
        assert mock_issues_protocol.issues_find.call_args.kwargs["fields"] is None

    async def test_fields_drop_undeclared_api_fields(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        # Tracker adds `self`, `id`, `version` and `favorite` to every projection,
        # and a queue's local fields come back as `<queue-id>--<key>`. None of them
        # are declared on `Issue`, so they land in the model's extras.
        issue = Issue.model_validate(
            {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
                "id": "593cd211ef7e8a33abcd1234",
                "key": "TEST-123",
                "version": 1,
                "favorite": False,
                "statusStartTime": "2024-01-01T00:00:00.000+0000",
                "queue": {"id": "1", "key": "TEST"},
                "694c13a2974fc069fc7db927--chapter": None,
            }
        )
        mock_issues_protocol.issues_find.return_value = page([issue])

        result = await client_session.call_tool(
            "issues_find", {"query": "Queue: TEST", "fields": ["key"]}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["values"] == [{"key": "TEST-123"}]

    async def test_description_selected_through_fields_is_kept(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        issue = Issue.model_construct(key="TEST-123", description="Body text")
        mock_issues_protocol.issues_find.return_value = page([issue])

        result = await client_session.call_tool(
            "issues_find",
            {"query": "Queue: TEST", "fields": ["key", "description"]},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        # `include_description` defaults to False, but asking for `description`
        # through `fields` is an explicit request for it.
        assert content["values"][0]["description"] == "Body text"


class TestIssuesCount:
    async def test_returns_count(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        mock_issues_protocol.issues_count.return_value = 42

        result = await client_session.call_tool(
            "issues_count", {"query": "Queue: TEST"}
        )

        assert not result.isError
        mock_issues_protocol.issues_count.assert_called_once()
        content = get_tool_result_content(result)
        # A named field, so the number cannot be mistaken for an HTTP status.
        assert content == {"count": 42}


class TestIssueGetWorklogs:
    async def test_returns_worklogs_for_multiple_issues(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklogs: list[Worklog],
    ) -> None:
        mock_issues_protocol.issue_get_worklogs.return_value = sample_worklogs

        result = await client_session.call_tool(
            "issue_get_worklogs", {"issue_ids": ["TEST-123", "TEST-124"]}
        )

        assert not result.isError
        # Should be called once per issue
        assert mock_issues_protocol.issue_get_worklogs.call_count == 2
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert "TEST-123" in content
        assert "TEST-124" in content
        assert len(content["TEST-123"]) == len(sample_worklogs)

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_get_worklogs", {"issue_ids": ["RESTRICTED-123"]}
        )

        assert result.isError
        mock_issues_protocol.issue_get_worklogs.assert_not_called()

    async def test_fields_filters_response(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_worklogs: list[Worklog],
    ) -> None:
        mock_issues_protocol.issue_get_worklogs.return_value = sample_worklogs

        result = await client_session.call_tool(
            "issue_get_worklogs",
            {"issue_ids": ["TEST-123"], "fields": ["comment"]},
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["TEST-123"][0]["comment"] == sample_worklogs[0].comment
        assert content["TEST-123"][0].get("createdBy") is None


class TestIssueGetAttachments:
    async def test_returns_attachments(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_attachments: list[IssueAttachment],
    ) -> None:
        mock_issues_protocol.issue_get_attachments.return_value = sample_attachments

        result = await client_session.call_tool(
            "issue_get_attachments", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_attachments.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_attachments)
        assert content[0]["name"] == sample_attachments[0].name

    async def test_fields_filters_response(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_attachments: list[IssueAttachment],
    ) -> None:
        mock_issues_protocol.issue_get_attachments.return_value = sample_attachments

        result = await client_session.call_tool(
            "issue_get_attachments", {"issue_id": "TEST-123", "fields": ["name"]}
        )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content[0]["name"] == sample_attachments[0].name
        assert content[0].get("content") is None


class TestIssueDownloadAttachment:
    async def test_saves_file_and_returns_metadata(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        file_content = b"hello attachment"
        attachment = IssueAttachment.model_construct(
            id="7698",
            name="image.png",
            mimetype="image/png",
        )
        mock_issues_protocol.issue_get_attachments.return_value = [attachment]

        async def _fake_download(
            issue_id: str,
            attachment_id: str,
            file_name: str,
            destination: Path,
            max_bytes: int,
            *,
            auth: object | None = None,
        ) -> int:
            destination.write_bytes(file_content)
            return len(file_content)

        mock_issues_protocol.issue_download_attachment.side_effect = _fake_download
        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-123",
                    "attachment_id": "7698",
                    "file_name": "image.png",
                    "save_directory": str(save_directory),
                },
            )

        assert not result.isError
        expected_path = save_directory.resolve() / "TEST-123-7698.png"
        expected_local_path = expected_path.relative_to(tmp_path.resolve())
        mock_issues_protocol.issue_get_attachments.assert_called_once()
        mock_issues_protocol.issue_download_attachment.assert_called_once()
        call_args = mock_issues_protocol.issue_download_attachment.call_args
        assert call_args.args == (
            "TEST-123",
            "7698",
            "image.png",
            expected_path,
            settings.tracker_max_attachment_bytes,
        )
        assert "auth" in call_args.kwargs
        content = get_tool_result_content(result)
        assert content == {
            "issue_id": "TEST-123",
            "attachment_id": "7698",
            "local_path": str(expected_local_path),
            "name": "TEST-123-7698.png",
            "original_name": "image.png",
            "mime_type": "image/png",
            "size": len(file_content),
        }
        assert content["name"] == expected_path.name
        assert expected_path.read_bytes() == file_content

    async def test_disk_name_matches_local_path_and_multi_suffix(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        attachment = IssueAttachment.model_construct(
            id="42",
            name="archive.tar.gz",
            mimetype="application/gzip",
        )
        mock_issues_protocol.issue_get_attachments.return_value = [attachment]
        mock_issues_protocol.issue_download_attachment.return_value = 3

        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-1",
                    "attachment_id": "42",
                    "file_name": "archive.tar.gz",
                    "save_directory": str(save_directory),
                },
            )

        assert not result.isError
        content = get_tool_result_content(result)
        expected_path = save_directory.resolve() / "TEST-1-42.gz"
        expected_local_path = expected_path.relative_to(tmp_path.resolve())
        assert content["local_path"] == str(expected_local_path)
        assert content["name"] == "TEST-1-42.gz"
        assert content["original_name"] == "archive.tar.gz"
        assert content["name"] == Path(content["local_path"]).name

    async def test_api_mime_type_overrides_extension(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        attachment = IssueAttachment.model_construct(
            id="7698",
            name="image.png",
            mimetype="application/pdf",
        )
        mock_issues_protocol.issue_get_attachments.return_value = [attachment]
        mock_issues_protocol.issue_download_attachment.return_value = 4

        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-123",
                    "attachment_id": "7698",
                    "file_name": "image.png",
                    "save_directory": str(save_directory),
                },
            )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["mime_type"] == "application/pdf"

    async def test_extensionless_uses_api_mime_type(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        attachment = IssueAttachment.model_construct(
            id="7698",
            name="export",
            mimetype="text/csv",
        )
        mock_issues_protocol.issue_get_attachments.return_value = [attachment]
        mock_issues_protocol.issue_download_attachment.return_value = 4

        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-123",
                    "attachment_id": "7698",
                    "file_name": "export",
                    "save_directory": str(save_directory),
                },
            )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["mime_type"] == "text/csv"
        assert content["name"] == "TEST-123-7698"
        assert content["original_name"] == "export"

    async def test_restricted_queue_raises_error(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            limit_queues=["ALLOWED", "PERMITTED"],
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "RESTRICTED-123",
                    "attachment_id": "7698",
                    "file_name": "image.png",
                    "save_directory": str(save_directory),
                },
            )

        assert result.isError
        mock_issues_protocol.issue_get_attachments.assert_not_called()
        mock_issues_protocol.issue_download_attachment.assert_not_called()

    async def test_protocol_not_found_error_propagates(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        mock_issues_protocol.issue_get_attachments.return_value = [
            IssueAttachment.model_construct(
                id="7698",
                name="image.png",
                mimetype="image/png",
            )
        ]
        mock_issues_protocol.issue_download_attachment.side_effect = AttachmentNotFound(
            "TEST-123",
            "7698",
            "image.png",
        )

        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-123",
                    "attachment_id": "7698",
                    "file_name": "image.png",
                    "save_directory": str(save_directory),
                },
            )

        assert result.isError

    async def test_path_resolve_error_propagates(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        outside_sandbox = tmp_path.parent / f"outside-{tmp_path.name}"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-123",
                    "attachment_id": "7698",
                    "file_name": "image.png",
                    "save_directory": str(outside_sandbox),
                },
            )

        assert result.isError
        mock_issues_protocol.issue_get_attachments.assert_not_called()
        mock_issues_protocol.issue_download_attachment.assert_not_called()

    async def test_missing_mime_type_returns_none(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        attachment = IssueAttachment.model_construct(
            id="7698",
            name="image.png",
            mimetype=None,
        )
        mock_issues_protocol.issue_get_attachments.return_value = [attachment]
        mock_issues_protocol.issue_download_attachment.return_value = 4

        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        async with safe_client_session(mcp_server) as client_session:
            result = await client_session.call_tool(
                "issue_download_attachment",
                {
                    "issue_id": "TEST-123",
                    "attachment_id": "7698",
                    "file_name": "image.png",
                    "save_directory": str(save_directory),
                },
            )

        assert not result.isError
        content = get_tool_result_content(result)
        assert content["mime_type"] is None

    async def test_multiple_attachments_correlate_by_ids_without_path_parsing(
        self,
        mock_app_context: AppContext,
        mock_issues_protocol: AsyncMock,
        tmp_path: Path,
    ) -> None:
        attachments = [
            IssueAttachment.model_construct(
                id="100",
                name="first.pdf",
                mimetype="application/pdf",
            ),
            IssueAttachment.model_construct(
                id="200",
                name="second.png",
                mimetype="image/png",
            ),
        ]
        mock_issues_protocol.issue_get_attachments.return_value = attachments

        async def _fake_download(
            issue_id: str,
            attachment_id: str,
            file_name: str,
            destination: Path,
            max_bytes: int,
            *,
            auth: object | None = None,
        ) -> int:
            destination.write_bytes(f"{attachment_id}:{file_name}".encode())
            return destination.stat().st_size

        mock_issues_protocol.issue_download_attachment.side_effect = _fake_download
        save_directory = tmp_path / "tracker-attachments"
        settings = create_test_settings(
            tracker_attachments_dir=str(tmp_path),
            attachment_download_enabled=True,
        )
        mcp_server = create_mcp_server(
            settings=settings,
            lifespan=make_test_lifespan(mock_app_context),
        )

        requests = [
            {
                "issue_id": "TEST-1",
                "attachment_id": "100",
                "file_name": "first.pdf",
                "save_directory": str(save_directory),
            },
            {
                "issue_id": "TEST-1",
                "attachment_id": "200",
                "file_name": "second.png",
                "save_directory": str(save_directory),
            },
        ]

        async with safe_client_session(mcp_server) as client_session:
            results = [
                await client_session.call_tool("issue_download_attachment", request)
                for request in requests
            ]

        assert all(not result.isError for result in results)
        downloaded = [get_tool_result_content(result) for result in results]

        for request, content in zip(requests, downloaded, strict=True):
            assert content["issue_id"] == request["issue_id"]
            assert content["attachment_id"] == request["attachment_id"]
            assert content["original_name"] == Path(request["file_name"]).name

        assert {item["attachment_id"] for item in downloaded} == {"100", "200"}
        assert {item["original_name"] for item in downloaded} == {
            "first.pdf",
            "second.png",
        }


class TestIssueGetChecklist:
    async def test_returns_checklist(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_checklist: list[ChecklistItem],
    ) -> None:
        mock_issues_protocol.issue_get_checklist.return_value = sample_checklist

        result = await client_session.call_tool(
            "issue_get_checklist", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_checklist.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_checklist)
        assert content[0]["text"] == sample_checklist[0].text


class TestIssueGetTransitions:
    async def test_returns_transitions(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_transitions: list[IssueTransition],
    ) -> None:
        mock_issues_protocol.issue_get_transitions.return_value = sample_transitions

        result = await client_session.call_tool(
            "issue_get_transitions", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_transitions.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, list)
        assert len(content) == len(sample_transitions)
        assert content[0]["id"] == sample_transitions[0].id
        assert content[0]["display"] == sample_transitions[0].display


class TestIssueGetChangelog:
    async def test_returns_changelog(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_changelog: ChangelogPage,
    ) -> None:
        mock_issues_protocol.issue_get_changelog.return_value = sample_changelog

        result = await client_session.call_tool(
            "issue_get_changelog", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        mock_issues_protocol.issue_get_changelog.assert_called_once()
        content = get_tool_result_content(result)
        assert isinstance(content, dict)
        assert content["next_cursor"] == sample_changelog.next_cursor
        entries = content["entries"]
        assert len(entries) == len(sample_changelog.entries)
        assert entries[0]["id"] == sample_changelog.entries[0].id
        assert entries[0]["type"] == sample_changelog.entries[0].type
        # `from` is serialized by its alias, not the python-safe `from_`,
        # and its full reference-object value must survive serialization
        assert entries[0]["fields"][0]["from"] == {
            "id": "1",
            "key": "open",
            "display": "Open",
        }
        # field display must survive serialization
        assert entries[0]["fields"][0]["field"]["display"] == "Status"

    async def test_surfaces_comment_and_trigger_payload(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        # A comment-type entry carries its payload in top-level `comments`/
        # `executedTriggers` rather than `fields`; both must reach the client.
        mock_issues_protocol.issue_get_changelog.return_value = ChangelogPage(
            entries=[
                ChangelogEntry(
                    id="c1",
                    type="IssueCommentAdded",
                    comments=ChangelogComments(
                        added=[ChangelogReference(id=98765, display="Looks good")]
                    ),
                    executed_triggers=[
                        ChangelogExecutedTrigger(
                            trigger=ChangelogReference(id=7, display="Auto-assign"),
                            success=True,
                            message="ok",
                        )
                    ],
                )
            ],
            next_cursor=None,
        )

        result = await client_session.call_tool(
            "issue_get_changelog", {"issue_id": "TEST-123"}
        )

        assert not result.isError
        entry = get_tool_result_content(result)["entries"][0]
        assert entry["comments"]["added"][0]["display"] == "Looks good"
        assert entry["executedTriggers"][0]["trigger"]["display"] == "Auto-assign"
        assert entry["executedTriggers"][0]["success"] is True

    async def test_passes_pagination_and_filters(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
        sample_changelog: ChangelogPage,
    ) -> None:
        mock_issues_protocol.issue_get_changelog.return_value = sample_changelog

        result = await client_session.call_tool(
            "issue_get_changelog",
            {
                "issue_id": "TEST-123",
                "per_page": 10,
                "cursor": "prev-entry-id",
                "field": "status",
                "type": "IssueWorkflow",
            },
        )

        assert not result.isError
        _, kwargs = mock_issues_protocol.issue_get_changelog.call_args
        assert kwargs["per_page"] == 10
        assert kwargs["cursor"] == "prev-entry-id"
        assert kwargs["field"] == "status"
        assert kwargs["type"] == "IssueWorkflow"

    async def test_restricted_queue_raises_error(
        self,
        client_session_with_limits: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session_with_limits.call_tool(
            "issue_get_changelog", {"issue_id": "RESTRICTED-123"}
        )

        assert result.isError
        mock_issues_protocol.issue_get_changelog.assert_not_called()

    async def test_rejects_non_positive_per_page(
        self,
        client_session: ClientSession,
        mock_issues_protocol: AsyncMock,
    ) -> None:
        result = await client_session.call_tool(
            "issue_get_changelog", {"issue_id": "TEST-123", "per_page": 0}
        )

        assert result.isError
        mock_issues_protocol.issue_get_changelog.assert_not_called()
