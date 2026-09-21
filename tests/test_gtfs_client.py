"""Verify GTFS download safeguards without allowing live HTTP in normal tests."""

import httpx
import pytest

from tests.gtfs_fixtures import minimal_gtfs_archive
from transport.integrations.gtfs.client import GTFSClient, GTFSDownloadError


def test_client_downloads_the_expected_zip_response() -> None:
    """Accept the expected archive content type, bounded length, and response content."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Record the request and return the valid synthetic archive with normal metadata."""
        requests.append(request)
        archive = minimal_gtfs_archive()
        return httpx.Response(
            200,
            content=archive,
            headers={"content-type": "application/zip", "content-length": str(len(archive))},
        )

    with GTFSClient(
        url="https://example.invalid/gtfs.zip", transport=httpx.MockTransport(respond)
    ) as client:
        assert client.download_archive() == minimal_gtfs_archive()
    assert str(requests[0].url) == "https://example.invalid/gtfs.zip"
    assert requests[0].headers["accept"] == "application/zip"


@pytest.mark.parametrize(
    "status, headers, content, message",
    [
        (503, {"content-type": "application/zip"}, b"", "download failed"),
        (200, {"content-type": "text/html"}, b"not a ZIP", "did not return a ZIP"),
        (
            200,
            {"content-type": "application/zip", "content-length": "not-a-number"},
            b"zip",
            "content length",
        ),
    ],
)
def test_client_normalizes_unusable_http_responses(
    status: int, headers: dict[str, str], content: bytes, message: str
) -> None:
    """Avoid exposing HTTP or malformed-source details to a future importer caller."""
    with (
        GTFSClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(status, headers=headers, content=content)
            )
        ) as client,
        pytest.raises(GTFSDownloadError, match=message),
    ):
        client.download_archive()
