from urllib.parse import quote

import pytest
from aioresponses import aioresponses

from mcp_tracker.tracker.custom.client import TrackerClient
from mcp_tracker.tracker.custom.errors import (
    AttachmentNotFound,
    AttachmentTooLarge,
    InvalidAttachmentIssueKey,
)
from tests.aioresponses_utils import RequestCapture

METADATA_URL = "https://api.tracker.yandex.net/v3/issues/TEST-123/attachments/17"


async def test_download_resolves_metadata_and_encodes_original_filename(
    tracker_client: TrackerClient,
) -> None:
    name = "скриншот / 1.png"
    data = b"\x89PNG\x00"
    capture = RequestCapture(payload={"id": "17", "name": name, "size": len(data)})
    with aioresponses() as mock:
        mock.get(METADATA_URL, callback=capture.callback)
        mock.get(
            f"{METADATA_URL}/{quote(name, safe='')}",
            body=data,
            content_type="image/png",
        )
        async with tracker_client.issue_open_attachment(
            "TEST-123", "17", max_bytes=len(data)
        ) as download:
            assert download.metadata.name == name
            assert download.mime_type == "image/png"
            assert download.charset is None
            assert b"".join([chunk async for chunk in download.chunks]) == data

    capture.assert_called_once()
    capture.last_request.assert_headers(
        {"Authorization": "OAuth test-token", "X-Org-ID": "test-org"}
    )


async def test_download_timeout_only_applies_to_the_content_request(
    tracker_client: TrackerClient,
) -> None:
    metadata = RequestCapture(payload={"id": "17", "name": "file.txt"})
    content = RequestCapture(body="abc")
    with aioresponses() as mock:
        mock.get(METADATA_URL, callback=metadata.callback)
        mock.get(f"{METADATA_URL}/file.txt", callback=content.callback)
        async with tracker_client.issue_open_attachment(
            "TEST-123", "17", max_bytes=4, timeout=120.0
        ) as download:
            assert await anext(download.chunks) == b"abc"

    assert metadata.last_request.timeout.total == 10.0
    assert content.last_request.timeout.total == 120.0


async def test_download_uses_charset_from_matching_response(
    tracker_client: TrackerClient,
) -> None:
    with aioresponses() as mock:
        mock.get(
            METADATA_URL,
            payload={"id": "17", "name": "file.txt", "mimetype": "TEXT/PLAIN"},
        )
        mock.get(
            f"{METADATA_URL}/file.txt",
            body=b"abc",
            content_type="text/plain; charset=windows-1251",
        )
        async with tracker_client.issue_open_attachment(
            "TEST-123", "17", max_bytes=4
        ) as download:
            assert download.mime_type == "text/plain"
            assert download.charset == "windows-1251"


@pytest.mark.parametrize(
    ("size", "content_length"),
    [(5, None), (None, "5"), (1, None)],
    ids=["metadata", "header", "actual-bytes"],
)
async def test_download_is_bounded(
    tracker_client: TrackerClient, size: int | None, content_length: str | None
) -> None:
    with aioresponses() as mock:
        mock.get(METADATA_URL, payload={"id": "17", "name": "file", "size": size})
        if size != 5:
            mock.get(
                f"{METADATA_URL}/file",
                body=b"abcde",
                headers={"Content-Length": content_length} if content_length else {},
            )
        with pytest.raises(AttachmentTooLarge, match="4-byte limit"):
            async with tracker_client.issue_open_attachment(
                "TEST-123", "17", max_bytes=4
            ) as download:
                await anext(download.chunks)


@pytest.mark.parametrize("stage", ["metadata", "content"])
async def test_attachment_not_found(tracker_client: TrackerClient, stage: str) -> None:
    with aioresponses() as mock:
        if stage == "metadata":
            mock.get(METADATA_URL, status=404)
        else:
            mock.get(METADATA_URL, payload={"id": "17", "name": "file"})
            mock.get(f"{METADATA_URL}/file", status=404)
        with pytest.raises(AttachmentNotFound, match="Attachment '17'"):
            async with tracker_client.issue_open_attachment(
                "TEST-123", "17", max_bytes=4
            ):
                pytest.fail("A missing attachment has no stream")


@pytest.mark.parametrize(
    ("issue_id", "attachment_id", "error"),
    [
        ("TEST-123/extra", "17", InvalidAttachmentIssueKey),
        ("TEST-123", "17/extra", AttachmentNotFound),
    ],
)
async def test_path_parameters_are_validated_before_http(
    tracker_client: TrackerClient,
    issue_id: str,
    attachment_id: str,
    error: type[Exception],
) -> None:
    with aioresponses() as mock:
        with pytest.raises(error):
            async with tracker_client.issue_open_attachment(
                issue_id, attachment_id, max_bytes=4
            ):
                pytest.fail("Invalid identifiers have no stream")
        assert not mock.requests
