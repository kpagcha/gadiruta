"""Assemble deterministic GTFS ZIP bytes from the small checked-in fixture feed."""

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def minimal_gtfs_archive() -> bytes:
    """Build the valid synthetic GTFS ZIP used by parser, client, and command tests."""
    fixture_directory = Path(__file__).parent / "fixtures" / "gtfs" / "minimal"
    archive_buffer = BytesIO()
    with ZipFile(archive_buffer, "w", compression=ZIP_DEFLATED) as archive:
        for fixture_path in sorted(fixture_directory.iterdir()):
            entry = ZipInfo(fixture_path.name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, fixture_path.read_bytes())
    return archive_buffer.getvalue()
