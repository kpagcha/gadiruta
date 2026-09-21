"""Persist validated GTFS archives as immutable datasets and atomically activate new imports."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from itertools import batched
from math import isfinite

from django.db import models, transaction
from django.utils import timezone

from transport.integrations.gtfs.feed import (
    inspect_gtfs_archive,
    iter_gtfs_table_rows,
)
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

BULK_CREATE_BATCH_SIZE = 1_000


class GTFSImportError(Exception):
    """A structurally valid GTFS archive cannot be imported into Gadiruta's transit schema."""


@dataclass(frozen=True)
class GTFSImportResult:
    """Describe whether an archive created a newly active dataset or was already known."""

    dataset_id: int
    archive_sha256: str
    status: str

    def as_dict(self) -> dict[str, object]:
        """Return stable JSON-ready output for the scheduled-import management command."""
        return {
            "dataset_id": self.dataset_id,
            "archive_sha256": self.archive_sha256,
            "status": self.status,
        }


def import_gtfs_archive(archive_bytes: bytes, *, source_url: str) -> GTFSImportResult:
    """Validate, persist, and atomically activate a previously unseen GTFS archive.

    A matching archive checksum is an idempotent no-op. A candidate dataset is not made active
    until every normalized table has been stored inside one transaction, so an import failure
    leaves the previous active dataset usable.
    """
    normalized_source_url = source_url.strip()
    if not normalized_source_url:
        raise GTFSImportError("GTFS import source URL cannot be blank.")
    inspection = inspect_gtfs_archive(archive_bytes)
    existing_dataset = GTFSFeedDataset.objects.filter(
        archive_sha256=inspection.archive_sha256
    ).first()
    if existing_dataset is not None:
        return _already_imported_result(existing_dataset)
    _validate_feed_relationships(archive_bytes)
    with transaction.atomic():
        existing_dataset = (
            GTFSFeedDataset.objects.select_for_update()
            .filter(archive_sha256=inspection.archive_sha256)
            .first()
        )
        if existing_dataset is not None:
            return _already_imported_result(existing_dataset)
        current_dataset = GTFSFeedDataset.objects.select_for_update().filter(is_active=True).first()
        dataset = GTFSFeedDataset.objects.create(
            source_url=normalized_source_url,
            archive_sha256=inspection.archive_sha256,
            service_start_date=_optional_service_date(inspection.service_start_date),
            service_end_date=_optional_service_date(inspection.service_end_date),
        )
        agency_ids = _insert_agencies(dataset, archive_bytes)
        stop_ids = _insert_stops(dataset, archive_bytes)
        route_ids = _insert_routes(dataset, archive_bytes, agency_ids)
        trip_ids = _insert_trips(dataset, archive_bytes, route_ids)
        _insert_stop_times(archive_bytes, trip_ids, stop_ids)
        _insert_calendar_services(dataset, archive_bytes)
        _insert_calendar_exceptions(dataset, archive_bytes)
        _insert_shape_points(dataset, archive_bytes)
        if current_dataset is not None:
            current_dataset.is_active = False
            current_dataset.save(update_fields=("is_active",))
        dataset.is_active = True
        dataset.activated_at = timezone.now()
        dataset.save(update_fields=("is_active", "activated_at"))
    return GTFSImportResult(
        dataset_id=dataset.pk,
        archive_sha256=inspection.archive_sha256,
        status="imported",
    )


def _already_imported_result(dataset: GTFSFeedDataset) -> GTFSImportResult:
    """Report a duplicate archive without altering its historic or active state."""
    return GTFSImportResult(
        dataset_id=dataset.pk,
        archive_sha256=dataset.archive_sha256,
        status="already_imported",
    )


def _validate_feed_relationships(archive_bytes: bytes) -> None:
    """Reject duplicate source keys and broken foreign references before database writes begin."""
    agency_ids = _unique_identifiers(archive_bytes, "agency.txt", "agency_id")
    stop_ids = _unique_identifiers(archive_bytes, "stops.txt", "stop_id")
    calendar_service_ids = _unique_identifiers(archive_bytes, "calendar.txt", "service_id")
    exception_service_ids = _validate_calendar_exceptions(archive_bytes)
    known_service_ids = calendar_service_ids | exception_service_ids
    route_ids = _validate_routes(archive_bytes, agency_ids)
    _validate_shape_points(archive_bytes)
    trip_ids = _validate_trips(archive_bytes, route_ids, known_service_ids)
    _validate_stop_times(archive_bytes, trip_ids, stop_ids)


def _unique_identifiers(archive_bytes: bytes, table_name: str, column_name: str) -> set[str]:
    """Return one table's unique trimmed source identifiers or explain the duplicate key."""
    identifiers: set[str] = set()
    for row in iter_gtfs_table_rows(archive_bytes, table_name):
        identifier = _value(row, column_name)
        if identifier in identifiers:
            raise GTFSImportError(
                f"GTFS table {table_name} has a duplicate {column_name}: {identifier!r}."
            )
        identifiers.add(identifier)
    return identifiers


def _validate_routes(archive_bytes: bytes, agency_ids: set[str]) -> set[str]:
    """Return unique routes after confirming every route belongs to a known agency."""
    route_ids: set[str] = set()
    for row in iter_gtfs_table_rows(archive_bytes, "routes.txt"):
        route_id = _value(row, "route_id")
        _add_unique_identifier(route_ids, route_id, "routes.txt", "route_id")
        agency_id = _value(row, "agency_id")
        _require_reference(agency_id, agency_ids, "routes.txt", "agency_id", "agency.txt")
        _integer_value(row, "route_type", "routes.txt")
    return route_ids


def _validate_calendar_exceptions(archive_bytes: bytes) -> set[str]:
    """Validate unique calendar-date overrides and return every referenced service identifier."""
    exception_keys: set[tuple[str, date]] = set()
    service_ids: set[str] = set()
    for row in iter_gtfs_table_rows(archive_bytes, "calendar_dates.txt"):
        service_id = _value(row, "service_id")
        exception_date = _date_value(row, "date", "calendar_dates.txt")
        key = (service_id, exception_date)
        if key in exception_keys:
            raise GTFSImportError(
                "GTFS table calendar_dates.txt has a duplicate service/date exception: "
                f"{service_id!r} on {exception_date.isoformat()}."
            )
        exception_keys.add(key)
        exception_type = _integer_value(row, "exception_type", "calendar_dates.txt")
        if exception_type not in {1, 2}:
            raise GTFSImportError(
                "GTFS table calendar_dates.txt has an unsupported exception type: "
                f"{exception_type!r}."
            )
        service_ids.add(service_id)
    return service_ids


def _validate_shape_points(archive_bytes: bytes) -> None:
    """Validate unique nonnegative shape-point sequences without requiring every trip geometry."""
    shape_point_keys: set[tuple[str, int]] = set()
    for row in iter_gtfs_table_rows(archive_bytes, "shapes.txt"):
        shape_id = _value(row, "shape_id")
        sequence = _nonnegative_integer_value(row, "shape_pt_sequence", "shapes.txt")
        key = (shape_id, sequence)
        if key in shape_point_keys:
            raise GTFSImportError(
                "GTFS table shapes.txt has a duplicate shape/sequence point: "
                f"{shape_id!r} at {sequence}."
            )
        shape_point_keys.add(key)
        _finite_float_value(row, "shape_pt_lat", "shapes.txt")
        _finite_float_value(row, "shape_pt_lon", "shapes.txt")


def _validate_trips(
    archive_bytes: bytes,
    route_ids: set[str],
    service_ids: set[str],
) -> set[str]:
    """Return unique trips after checking their schedule-critical route and calendar references."""
    trip_ids: set[str] = set()
    for row in iter_gtfs_table_rows(archive_bytes, "trips.txt"):
        trip_id = _value(row, "trip_id")
        _add_unique_identifier(trip_ids, trip_id, "trips.txt", "trip_id")
        _require_reference(
            _value(row, "route_id"), route_ids, "trips.txt", "route_id", "routes.txt"
        )
        _require_reference(
            _value(row, "service_id"),
            service_ids,
            "trips.txt",
            "service_id",
            "calendar.txt or calendar_dates.txt",
        )
        direction_id = _optional_integer_value(row, "direction_id", "trips.txt")
        if direction_id is not None and direction_id not in {0, 1}:
            raise GTFSImportError(
                f"GTFS table trips.txt has an unsupported direction_id: {direction_id!r}."
            )
    return trip_ids


def _validate_stop_times(
    archive_bytes: bytes,
    trip_ids: set[str],
    stop_ids: set[str],
) -> None:
    """Validate direct-journey stop calls before writing their large ordered table in batches."""
    stop_time_keys: set[tuple[str, int]] = set()
    for row in iter_gtfs_table_rows(archive_bytes, "stop_times.txt"):
        trip_id = _value(row, "trip_id")
        _require_reference(trip_id, trip_ids, "stop_times.txt", "trip_id", "trips.txt")
        _require_reference(
            _value(row, "stop_id"), stop_ids, "stop_times.txt", "stop_id", "stops.txt"
        )
        sequence = _nonnegative_integer_value(row, "stop_sequence", "stop_times.txt")
        key = (trip_id, sequence)
        if key in stop_time_keys:
            raise GTFSImportError(
                "GTFS table stop_times.txt has a duplicate trip/sequence stop call: "
                f"{trip_id!r} at {sequence}."
            )
        stop_time_keys.add(key)
        _time_seconds_value(row, "arrival_time", "stop_times.txt")
        _time_seconds_value(row, "departure_time", "stop_times.txt")
        _optional_nonnegative_integer_value(row, "pickup_type", "stop_times.txt")
        _optional_nonnegative_integer_value(row, "drop_off_type", "stop_times.txt")


def _insert_agencies(dataset: GTFSFeedDataset, archive_bytes: bytes) -> dict[str, int]:
    """Store all feed agencies and return their database IDs by source identifier."""
    _bulk_create_in_batches(
        GTFSAgency,
        (
            GTFSAgency(
                dataset=dataset,
                external_id=_value(row, "agency_id"),
                name=_value(row, "agency_name"),
                url=_value(row, "agency_url"),
                timezone=_value(row, "agency_timezone"),
                phone=_optional_value(row, "agency_phone"),
                language=_optional_value(row, "agency_lang"),
                fare_url=_optional_value(row, "agency_fare_url"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "agency.txt")
        ),
    )
    return _database_ids_by_external_id(GTFSAgency, dataset)


def _insert_stops(dataset: GTFSFeedDataset, archive_bytes: bytes) -> dict[str, int]:
    """Store all physical stops and return their database IDs by source identifier."""
    _bulk_create_in_batches(
        GTFSStop,
        (
            GTFSStop(
                dataset=dataset,
                external_id=_value(row, "stop_id"),
                name=_value(row, "stop_name"),
                latitude=_finite_float_value(row, "stop_lat", "stops.txt"),
                longitude=_finite_float_value(row, "stop_lon", "stops.txt"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "stops.txt")
        ),
    )
    return _database_ids_by_external_id(GTFSStop, dataset)


def _insert_routes(
    dataset: GTFSFeedDataset,
    archive_bytes: bytes,
    agency_ids: dict[str, int],
) -> dict[str, int]:
    """Store routes with their resolved agency foreign keys and return IDs by source identifier."""
    _bulk_create_in_batches(
        GTFSRoute,
        (
            GTFSRoute(
                dataset=dataset,
                agency_id=agency_ids[_value(row, "agency_id")],
                external_id=_value(row, "route_id"),
                short_name=_value(row, "route_short_name"),
                long_name=_value(row, "route_long_name"),
                route_type=_integer_value(row, "route_type", "routes.txt"),
                url=_optional_value(row, "route_url"),
                color=_optional_value(row, "route_color"),
                text_color=_optional_value(row, "route_text_color"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "routes.txt")
        ),
    )
    return _database_ids_by_external_id(GTFSRoute, dataset)


def _insert_trips(
    dataset: GTFSFeedDataset,
    archive_bytes: bytes,
    route_ids: dict[str, int],
) -> dict[str, int]:
    """Store trips with their resolved route foreign keys and return IDs by source identifier."""
    _bulk_create_in_batches(
        GTFSTrip,
        (
            GTFSTrip(
                dataset=dataset,
                route_id=route_ids[_value(row, "route_id")],
                external_id=_value(row, "trip_id"),
                service_id=_value(row, "service_id"),
                headsign=_optional_value(row, "trip_headsign"),
                direction_id=_optional_integer_value(row, "direction_id", "trips.txt"),
                shape_external_id=_optional_value(row, "shape_id"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "trips.txt")
        ),
    )
    return _database_ids_by_external_id(GTFSTrip, dataset)


def _insert_stop_times(
    archive_bytes: bytes,
    trip_ids: dict[str, int],
    stop_ids: dict[str, int],
) -> None:
    """Store potentially large stop-time data in bounded batches after relationship validation."""
    _bulk_create_in_batches(
        GTFSStopTime,
        (
            GTFSStopTime(
                trip_id=trip_ids[_value(row, "trip_id")],
                stop_id=stop_ids[_value(row, "stop_id")],
                arrival_seconds=_time_seconds_value(row, "arrival_time", "stop_times.txt"),
                departure_seconds=_time_seconds_value(row, "departure_time", "stop_times.txt"),
                sequence=_nonnegative_integer_value(row, "stop_sequence", "stop_times.txt"),
                pickup_type=_optional_nonnegative_integer_value(
                    row, "pickup_type", "stop_times.txt"
                ),
                drop_off_type=_optional_nonnegative_integer_value(
                    row, "drop_off_type", "stop_times.txt"
                ),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "stop_times.txt")
        ),
    )


def _insert_calendar_services(dataset: GTFSFeedDataset, archive_bytes: bytes) -> None:
    """Store the regular weekly calendar rules used to resolve an active service date."""
    _bulk_create_in_batches(
        GTFSCalendarService,
        (
            GTFSCalendarService(
                dataset=dataset,
                service_id=_value(row, "service_id"),
                monday=_boolean_value(row, "monday", "calendar.txt"),
                tuesday=_boolean_value(row, "tuesday", "calendar.txt"),
                wednesday=_boolean_value(row, "wednesday", "calendar.txt"),
                thursday=_boolean_value(row, "thursday", "calendar.txt"),
                friday=_boolean_value(row, "friday", "calendar.txt"),
                saturday=_boolean_value(row, "saturday", "calendar.txt"),
                sunday=_boolean_value(row, "sunday", "calendar.txt"),
                start_date=_date_value(row, "start_date", "calendar.txt"),
                end_date=_date_value(row, "end_date", "calendar.txt"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "calendar.txt")
        ),
    )


def _insert_calendar_exceptions(dataset: GTFSFeedDataset, archive_bytes: bytes) -> None:
    """Store explicit service additions and removals which override regular weekly calendars."""
    _bulk_create_in_batches(
        GTFSCalendarException,
        (
            GTFSCalendarException(
                dataset=dataset,
                service_id=_value(row, "service_id"),
                date=_date_value(row, "date", "calendar_dates.txt"),
                exception_type=_integer_value(row, "exception_type", "calendar_dates.txt"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "calendar_dates.txt")
        ),
    )


def _insert_shape_points(dataset: GTFSFeedDataset, archive_bytes: bytes) -> None:
    """Store potentially large route-shape coordinates in bounded batches for future map use."""
    _bulk_create_in_batches(
        GTFSShapePoint,
        (
            GTFSShapePoint(
                dataset=dataset,
                shape_external_id=_value(row, "shape_id"),
                latitude=_finite_float_value(row, "shape_pt_lat", "shapes.txt"),
                longitude=_finite_float_value(row, "shape_pt_lon", "shapes.txt"),
                sequence=_nonnegative_integer_value(row, "shape_pt_sequence", "shapes.txt"),
            )
            for row in iter_gtfs_table_rows(archive_bytes, "shapes.txt")
        ),
    )


def _bulk_create_in_batches(
    model_class: type[models.Model],
    records: Iterable[models.Model],
) -> None:
    """Insert model records in bounded batches to keep full-feed imports memory-safe."""
    for batch in batched(records, BULK_CREATE_BATCH_SIZE, strict=False):
        model_class.objects.bulk_create(batch, batch_size=BULK_CREATE_BATCH_SIZE)


def _database_ids_by_external_id(
    model_class: type[GTFSAgency] | type[GTFSRoute] | type[GTFSStop] | type[GTFSTrip],
    dataset: GTFSFeedDataset,
) -> dict[str, int]:
    """Return persisted feed-scoped IDs for resolving dependent model foreign keys efficiently."""
    return dict(model_class.objects.filter(dataset=dataset).values_list("external_id", "id"))


def _add_unique_identifier(
    identifiers: set[str],
    identifier: str,
    table_name: str,
    column_name: str,
) -> None:
    """Add one source key or reject duplicates before the database reports an ambiguous error."""
    if identifier in identifiers:
        raise GTFSImportError(
            f"GTFS table {table_name} has a duplicate {column_name}: {identifier!r}."
        )
    identifiers.add(identifier)


def _require_reference(
    identifier: str,
    identifiers: set[str],
    table_name: str,
    column_name: str,
    target_table_name: str,
) -> None:
    """Require one source foreign key to reference an identifier in its declared GTFS table."""
    if identifier not in identifiers:
        raise GTFSImportError(
            f"GTFS table {table_name} references an unknown {column_name} {identifier!r} "
            f"in {target_table_name}."
        )


def _optional_service_date(value: str | None) -> date | None:
    """Convert an inspection's optional basic-format service bound into a Python date."""
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as error:
        raise GTFSImportError(
            f"GTFS inspection contains an invalid service date: {value!r}."
        ) from error


def _value(row: dict[str, str], column_name: str) -> str:
    """Return one already-validated required CSV value with incidental whitespace removed."""
    return row[column_name].strip()


def _optional_value(row: dict[str, str], column_name: str) -> str:
    """Return an optional GTFS CSV field as a trimmed string when its header is available."""
    return row.get(column_name, "").strip()


def _integer_value(row: dict[str, str], column_name: str, table_name: str) -> int:
    """Parse one GTFS integral value and raise a source-specific import failure if malformed."""
    raw_value = _value(row, column_name)
    try:
        return int(raw_value)
    except ValueError as error:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid integer {column_name}: {raw_value!r}."
        ) from error


def _nonnegative_integer_value(row: dict[str, str], column_name: str, table_name: str) -> int:
    """Parse one nonnegative GTFS sequence number used by ordered database records."""
    value = _integer_value(row, column_name, table_name)
    if value < 0:
        raise GTFSImportError(f"GTFS table {table_name} has a negative {column_name}: {value!r}.")
    return value


def _optional_integer_value(row: dict[str, str], column_name: str, table_name: str) -> int | None:
    """Parse an optional integer field, retaining absent GTFS values as database nulls."""
    raw_value = _optional_value(row, column_name)
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError as error:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid integer {column_name}: {raw_value!r}."
        ) from error


def _optional_nonnegative_integer_value(
    row: dict[str, str], column_name: str, table_name: str
) -> int | None:
    """Parse an optional nonnegative service-call code that maps to a positive-small DB field."""
    value = _optional_integer_value(row, column_name, table_name)
    if value is not None and value < 0:
        raise GTFSImportError(f"GTFS table {table_name} has a negative {column_name}: {value!r}.")
    return value


def _boolean_value(row: dict[str, str], column_name: str, table_name: str) -> bool:
    """Parse one GTFS 0/1 service-calendar flag without silently accepting arbitrary integers."""
    raw_value = _value(row, column_name)
    if raw_value not in {"0", "1"}:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid boolean {column_name}: {raw_value!r}."
        )
    return raw_value == "1"


def _date_value(row: dict[str, str], column_name: str, table_name: str) -> date:
    """Parse a required GTFS basic-format date into the database's date representation."""
    raw_value = _value(row, column_name)
    try:
        return datetime.strptime(raw_value, "%Y%m%d").date()
    except ValueError as error:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid date {column_name}: {raw_value!r}."
        ) from error


def _time_seconds_value(row: dict[str, str], column_name: str, table_name: str) -> int:
    """Convert a GTFS service-day time, including values beyond 24:00, into elapsed seconds."""
    raw_value = _value(row, column_name)
    parts = raw_value.split(":")
    if len(parts) != 3:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid time {column_name}: {raw_value!r}."
        )
    try:
        hours, minutes, seconds = (int(part) for part in parts)
    except ValueError as error:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid time {column_name}: {raw_value!r}."
        ) from error
    if hours < 0 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid time {column_name}: {raw_value!r}."
        )
    return (hours * 60 * 60) + (minutes * 60) + seconds


def _finite_float_value(row: dict[str, str], column_name: str, table_name: str) -> float:
    """Parse finite geographic coordinates while rejecting malformed, NaN, and infinite values."""
    raw_value = _value(row, column_name)
    try:
        value = float(raw_value)
    except ValueError as error:
        raise GTFSImportError(
            f"GTFS table {table_name} has an invalid decimal {column_name}: {raw_value!r}."
        ) from error
    if not isfinite(value):
        raise GTFSImportError(
            f"GTFS table {table_name} has a non-finite decimal {column_name}: {raw_value!r}."
        )
    return value
