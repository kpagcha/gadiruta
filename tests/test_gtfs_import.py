"""Verify atomic persistence and activation of normalized GTFS archives."""

from datetime import date
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from tests.gtfs_fixtures import minimal_gtfs_archive
from transport.models import (
    GTFSAgency,
    GTFSCalendarException,
    GTFSCalendarService,
    GTFSFeedDataset,
    GTFSRoute,
    GTFSShapePoint,
    GTFSStop,
    GTFSStopTime,
    GTFSTrip,
)
from transport.services.gtfs_import import GTFSImportError, import_gtfs_archive


def replace_gtfs_table(archive_bytes: bytes, table_name: str, replacement: str) -> bytes:
    """Return a deterministic archive copy with exactly one fixture table's text replaced."""
    output = BytesIO()
    with (
        ZipFile(BytesIO(archive_bytes)) as source,
        ZipFile(output, "w", compression=ZIP_DEFLATED) as destination,
    ):
        for entry in source.infolist():
            contents = replacement.encode() if entry.filename == table_name else source.read(entry)
            destination.writestr(entry.filename, contents)
    return output.getvalue()


@pytest.mark.django_db
def test_import_persists_normalized_feed_rows_and_activates_the_dataset() -> None:
    """Import each required GTFS table with normalized dates, times, and source relationships."""
    result = import_gtfs_archive(
        minimal_gtfs_archive(), source_url="https://example.invalid/gtfs.zip"
    )
    dataset = GTFSFeedDataset.objects.get(pk=result.dataset_id)
    assert result.status == "imported"
    assert dataset.is_active is True
    assert dataset.service_start_date == date(2026, 1, 1)
    assert dataset.service_end_date == date(2026, 12, 31)
    assert GTFSAgency.objects.filter(dataset=dataset).count() == 1
    assert GTFSStop.objects.filter(dataset=dataset).count() == 3
    assert GTFSRoute.objects.filter(dataset=dataset).count() == 1
    assert GTFSTrip.objects.filter(dataset=dataset).count() == 1
    assert GTFSStopTime.objects.filter(trip__dataset=dataset).count() == 3
    assert GTFSCalendarService.objects.filter(dataset=dataset).count() == 1
    assert GTFSCalendarException.objects.filter(dataset=dataset).count() == 2
    assert GTFSShapePoint.objects.filter(dataset=dataset).count() == 3
    stop_time = GTFSStopTime.objects.select_related("trip", "stop").get(
        trip__dataset=dataset,
        sequence=3,
    )
    assert stop_time.arrival_seconds == 9 * 60 * 60
    assert stop_time.departure_seconds == 9 * 60 * 60
    assert stop_time.trip.route.short_name == "M-050"
    assert stop_time.stop.external_id == "jerez-1"


@pytest.mark.django_db
def test_import_deactivates_the_previous_dataset_only_after_the_new_data_is_persisted() -> None:
    """Switch active datasets at transaction end while retaining the preceding import history."""
    previous_dataset = GTFSFeedDataset.objects.create(
        source_url="https://example.invalid/previous.zip",
        archive_sha256="0" * 64,
        is_active=True,
    )
    result = import_gtfs_archive(
        minimal_gtfs_archive(), source_url="https://example.invalid/gtfs.zip"
    )
    previous_dataset.refresh_from_db()
    active_dataset = GTFSFeedDataset.objects.get(pk=result.dataset_id)
    assert previous_dataset.is_active is False
    assert active_dataset.is_active is True
    assert GTFSFeedDataset.objects.filter(is_active=True).count() == 1


@pytest.mark.django_db
def test_invalid_relationship_keeps_the_existing_active_dataset_unchanged() -> None:
    """Reject source references before any candidate rows can displace usable schedule data."""
    previous_dataset = GTFSFeedDataset.objects.create(
        source_url="https://example.invalid/previous.zip",
        archive_sha256="0" * 64,
        is_active=True,
    )
    invalid_archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "routes.txt",
        "route_id,agency_id,route_short_name,route_long_name,route_type\n"
        "cadiz-jerez,missing-agency,M-050,Cádiz - Jerez,3\n",
    )
    with pytest.raises(GTFSImportError, match="unknown agency_id"):
        import_gtfs_archive(invalid_archive, source_url="https://example.invalid/gtfs.zip")
    previous_dataset.refresh_from_db()
    assert previous_dataset.is_active is True
    assert GTFSFeedDataset.objects.count() == 1


@pytest.mark.django_db
def test_reimporting_identical_archive_is_an_idempotent_no_op() -> None:
    """Retain the originally imported immutable dataset when the scheduled feed is unchanged."""
    first_result = import_gtfs_archive(
        minimal_gtfs_archive(), source_url="https://example.invalid/gtfs.zip"
    )
    second_result = import_gtfs_archive(
        minimal_gtfs_archive(), source_url="https://example.invalid/other-source.zip"
    )
    assert second_result.status == "already_imported"
    assert second_result.dataset_id == first_result.dataset_id
    assert GTFSFeedDataset.objects.count() == 1
    assert GTFSFeedDataset.objects.get(pk=first_result.dataset_id).source_url.endswith("gtfs.zip")


@pytest.mark.django_db
def test_import_accepts_zero_based_shape_sequences() -> None:
    """Preserve CTAN's valid zero-based shape-point ordering instead of treating it as an error."""
    archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "shapes.txt",
        "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
        "cadiz-jerez-shape,36.5297,-6.2921,0\n"
        "cadiz-jerez-shape,36.6000,-6.2100,1\n"
        "cadiz-jerez-shape,36.6850,-6.1261,2\n",
    )
    result = import_gtfs_archive(archive, source_url="https://example.invalid/gtfs.zip")
    assert GTFSShapePoint.objects.get(dataset_id=result.dataset_id, sequence=0).latitude == 36.5297


@pytest.mark.django_db
def test_import_retains_a_trip_with_unavailable_optional_shape_geometry() -> None:
    """Keep timetable data usable when CTAN omits the optional shape referenced by a trip."""
    archive = replace_gtfs_table(
        minimal_gtfs_archive(),
        "trips.txt",
        "route_id,service_id,trip_id,trip_headsign,direction_id,shape_id\n"
        "cadiz-jerez,weekday,cadiz-jerez-0800,Jerez,0,unavailable-shape\n",
    )
    result = import_gtfs_archive(archive, source_url="https://example.invalid/gtfs.zip")
    assert (
        GTFSTrip.objects.get(dataset_id=result.dataset_id).shape_external_id == "unavailable-shape"
    )
