"""Import and atomically activate a local or CTAN-hosted GTFS archive."""

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from django.core.management.base import BaseCommand, CommandError

from transport.integrations.gtfs.client import GTFS_FEED_URL, GTFSClient, GTFSDownloadError
from transport.integrations.gtfs.feed import GTFSFeedError
from transport.services.gtfs_import import GTFSImportError, import_gtfs_archive


class Command(BaseCommand):
    """Persist a validated GTFS dataset and switch live queries to it only after full success."""

    help = "Download or read a GTFS ZIP archive, import it, and atomically activate the dataset."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Accept either a local archive path or an override URL for controlled imports."""
        source_group = parser.add_mutually_exclusive_group()
        source_group.add_argument("--file", type=Path, help="Read a GTFS ZIP archive from disk.")
        source_group.add_argument(
            "--url", default=GTFS_FEED_URL, help="Download a GTFS ZIP archive."
        )

    def handle(self, *args: object, **options: object) -> None:
        """Load a feed, atomically import it, and print a concise machine-readable result."""
        file_path = cast(Path | None, options["file"])
        if file_path is not None:
            try:
                resolved_path = file_path.resolve(strict=True)
                archive = resolved_path.read_bytes()
            except OSError as error:
                raise CommandError(f"Could not read GTFS archive: {file_path}") from error
            source_url = resolved_path.as_uri()
            source = str(resolved_path)
        else:
            source_url = cast(str, options["url"])
            try:
                with GTFSClient(url=source_url) as client:
                    archive = client.download_archive()
            except GTFSDownloadError as error:
                raise CommandError(str(error)) from error
            source = source_url
        try:
            result = import_gtfs_archive(archive, source_url=source_url)
        except (GTFSFeedError, GTFSImportError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            json.dumps({"source": source, **result.as_dict()}, indent=2, sort_keys=True)
        )
