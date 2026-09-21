"""Verify the non-mutating GTFS inspection command against a local fixture archive."""

import json
from io import StringIO
from pathlib import Path

from django.core.management import call_command

from tests.gtfs_fixtures import minimal_gtfs_archive


def test_command_inspects_a_local_archive_without_network(tmp_path: Path) -> None:
    """Print the archive source and structural summary for a developer-supplied local ZIP."""
    archive_path = tmp_path / "minimal-gtfs.zip"
    archive_path.write_bytes(minimal_gtfs_archive())
    output = StringIO()
    call_command("inspect_gtfs", "--file", archive_path, stdout=output)
    report = json.loads(output.getvalue())
    assert report["source"] == str(archive_path)
    assert report["tables"]["stop_times.txt"] == 3
    assert report["route_type_counts"] == {"3": 1}
