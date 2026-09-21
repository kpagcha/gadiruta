"""Download CTAN's published GTFS archive with bounded, normalized HTTP failures."""

from types import TracebackType
from typing import Self

import httpx

GTFS_FEED_URL = "https://api.ctan.es/v1/datos/UNIFICADO/gtfs.zip"
MAX_ARCHIVE_BYTES = 25 * 1024 * 1024


class GTFSDownloadError(Exception):
    """The GTFS source could not provide a usable archive download."""


class GTFSClient:
    """Own a synchronous HTTP session for one bounded GTFS archive download."""

    def __init__(
        self,
        *,
        url: str = GTFS_FEED_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Configure a downloadable GTFS URL and optional mock transport for offline tests."""
        self._url = url
        self._http = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=5.0),
            headers={"Accept": "application/zip"},
            transport=transport,
        )

    def __enter__(self) -> Self:
        """Return this client for one managed GTFS retrieval."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the owned HTTP client without hiding exceptions from the caller."""
        self._http.close()

    def download_archive(self) -> bytes:
        """Download one plausibly sized ZIP response or raise a stable source error."""
        try:
            response = self._http.get(self._url)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise GTFSDownloadError("GTFS archive download failed.") from error
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type not in {"application/zip", "application/x-zip-compressed"}:
            raise GTFSDownloadError("GTFS source did not return a ZIP archive.")
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError as error:
                raise GTFSDownloadError(
                    "GTFS source returned an invalid content length."
                ) from error
            if declared_size < 1 or declared_size > MAX_ARCHIVE_BYTES:
                raise GTFSDownloadError("GTFS archive exceeds the download size limit.")
        archive = response.content
        if not archive or len(archive) > MAX_ARCHIVE_BYTES:
            raise GTFSDownloadError("GTFS archive exceeds the download size limit.")
        return archive
