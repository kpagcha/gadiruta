"""Verify the persistent GTFS import command with a deterministic local archive."""

import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from tests.gtfs_fixtures import minimal_gtfs_archive
from transport.models import GTFSFeedDataset


@pytest.mark.django_db
def test_command_imports_a_local_archive_and_reports_the_active_dataset(tmp_path: Path) -> None:
    """Allow local developer imports without a live CTAN HTTP request or raw database access."""
    archive_path = tmp_path / "minimal-gtfs.zip"
    archive_path.write_bytes(minimal_gtfs_archive())
    output = StringIO()
    call_command("import_gtfs", "--file", archive_path, stdout=output)
    report = json.loads(output.getvalue())
    assert report["source"] == str(archive_path)
    assert report["status"] == "imported"
    assert GTFSFeedDataset.objects.get(pk=report["dataset_id"]).is_active is True
