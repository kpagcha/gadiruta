"""Refresh active GTFS place-to-stop links from CTAN's physical-stop catalogue."""

import json

from django.core.management.base import BaseCommand, CommandError

from transport.services.ctan_gtfs_links import (
    CTANGTFSLinkError,
    refresh_active_ctan_gtfs_place_stop_links,
)


class Command(BaseCommand):
    """Link canonical population centres to the active feed's matching physical GTFS stops."""

    help = "Refresh active GTFS place-to-stop links from CTAN's physical-stop catalogue."

    def handle(self, *args: object, **options: object) -> None:
        """Retrieve CTAN metadata, replace links for the active dataset, and print a summary."""
        try:
            result = refresh_active_ctan_gtfs_place_stop_links()
        except CTANGTFSLinkError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps(result.as_dict(), indent=2, sort_keys=True))
