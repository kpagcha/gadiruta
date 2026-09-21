"""Inspect a local or CTAN-hosted GTFS archive before persistent import is introduced."""

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from django.core.management.base import BaseCommand, CommandError

from transport.integrations.gtfs.client import GTFS_FEED_URL, GTFSClient, GTFSDownloadError
from transport.integrations.gtfs.feed import GTFSFeedError, inspect_gtfs_archive


class Command(BaseCommand):
    """Report a structurally validated GTFS archive without modifying the database."""

    help = "Download or read a GTFS ZIP archive and print a JSON structural inspection."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Accept either a local archive path or an override URL for controlled discovery."""
        source_group = parser.add_mutually_exclusive_group()
        source_group.add_argument("--file", type=Path, help="Read a GTFS ZIP archive from disk.")
        source_group.add_argument(
            "--url", default=GTFS_FEED_URL, help="Download a GTFS ZIP archive."
        )

    def handle(self, *args: object, **options: object) -> None:
        """Load, validate, and print one GTFS inspection without retaining source rows."""
        file_path = cast(Path | None, options["file"])
        if file_path is not None:
            try:
                archive = file_path.read_bytes()
            except OSError as error:
                raise CommandError(f"Could not read GTFS archive: {file_path}") from error
            source = str(file_path)
        else:
            url = cast(str, options["url"])
            try:
                with GTFSClient(url=url) as client:
                    archive = client.download_archive()
            except GTFSDownloadError as error:
                raise CommandError(str(error)) from error
            source = url
        try:
            inspection = inspect_gtfs_archive(archive)
        except GTFSFeedError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            json.dumps({"source": source, **inspection.as_dict()}, indent=2, sort_keys=True)
        )
