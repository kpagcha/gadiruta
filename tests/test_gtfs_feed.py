"""Verify deterministic structural validation and inspection of compact GTFS archives."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from tests.gtfs_fixtures import minimal_gtfs_archive
from transport.integrations.gtfs.feed import GTFSFeedError, inspect_gtfs_archive


def replace_gtfs_table(archive_bytes: bytes, table_name: str, replacement: str) -> bytes:
    """Return fixture archive bytes with exactly one table replaced for one failure scenario."""
    source = ZipFile(BytesIO(archive_bytes))
    target_buffer = BytesIO()
    with source, ZipFile(target_buffer, "w", compression=ZIP_DEFLATED) as target:
        for entry in source.infolist():
            content = replacement.encode() if entry.filename == table_name else source.read(entry)
            target.writestr(entry.filename, content)
    return target_buffer.getvalue()


def test_inspection_summarizes_the_valid_minimal_feed() -> None:
    """Report stable checksums, row counts, modes, agencies, and service-date bounds."""
    inspection = inspect_gtfs_archive(minimal_gtfs_archive())
    assert inspection.as_dict() == {
        "archive_sha256": "dd531bb5c310587443b4cb71a7ef843b413f65b4d06f19b0e53a82fd26050446",
        "tables": {
            "agency.txt": 1,
            "stops.txt": 3,
            "routes.txt": 1,
            "trips.txt": 1,
            "stop_times.txt": 3,
            "calendar.txt": 1,
            "calendar_dates.txt": 2,
            "shapes.txt": 3,
        },
        "agency_names": ["Cádiz Bus"],
        "route_type_counts": {"3": 1},
        "service_start_date": "20260101",
        "service_end_date": "20261231",
    }


def test_missing_required_column_is_rejected() -> None:
    """Reject a feed that cannot supply the local direct-journey query's stop sequence."""
    archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "stop_times.txt",
        "trip_id,arrival_time,departure_time,stop_id\ncadiz-jerez-0800,08:00:00,08:00:00,cadiz-1\n",
    )
    with pytest.raises(GTFSFeedError, match="stop_sequence"):
        inspect_gtfs_archive(archive)


def test_whitespace_around_header_names_is_normalized() -> None:
    """Accept CTAN's observed leading whitespace in the agency-name header field."""
    archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "agency.txt",
        "agency_id, agency_name,agency_url,agency_timezone\n"
        "cadiz-bus,Cádiz Bus,https://example.invalid,Europe/Madrid\n",
    )
    assert inspect_gtfs_archive(archive).agency_names == ("Cádiz Bus",)


def test_unescaped_quotes_in_display_names_do_not_corrupt_stop_columns() -> None:
    """Accept CTAN's known non-standard quote formatting while retaining complete stop rows."""
    archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "stops.txt",
        'stop_id,stop_name,stop_lat,stop_lon\ncadiz-1,"Oasis " Viveros "",36.5297,-6.2921\n',
    )
    inspection = inspect_gtfs_archive(archive)
    assert {table.name: table.row_count for table in inspection.tables}["stops.txt"] == 1


def test_invalid_service_date_is_rejected() -> None:
    """Reject invalid calendar dates before a later importer could activate bad service data."""
    archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "calendar_dates.txt",
        "service_id,date,exception_type\nweekday,20261301,1\n",
    )
    with pytest.raises(GTFSFeedError, match="invalid service date"):
        inspect_gtfs_archive(archive)


def test_non_zip_bytes_are_rejected() -> None:
    """Normalize malformed archive bytes to the GTFS integration's stable validation error."""
    with pytest.raises(GTFSFeedError, match="valid ZIP archive"):
        inspect_gtfs_archive(b"not a ZIP archive")
