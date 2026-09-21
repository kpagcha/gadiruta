"""Validate and inspect the GTFS archive shape required for Gadiruta's local import."""

import csv
import hashlib
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO, TextIOWrapper
from zipfile import BadZipFile, ZipFile, ZipInfo

MAX_UNCOMPRESSED_ARCHIVE_BYTES = 100 * 1024 * 1024
REQUIRED_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "agency.txt": ("agency_id", "agency_name"),
    "stops.txt": ("stop_id", "stop_name", "stop_lat", "stop_lon"),
    "routes.txt": ("route_id", "agency_id", "route_short_name", "route_long_name", "route_type"),
    "trips.txt": ("route_id", "service_id", "trip_id"),
    "stop_times.txt": (
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    ),
    "calendar.txt": (
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ),
    "calendar_dates.txt": ("service_id", "date", "exception_type"),
    "shapes.txt": ("shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"),
}


class GTFSFeedError(Exception):
    """A GTFS archive cannot be safely inspected or imported."""


@dataclass(frozen=True)
class GTFSTableInspection:
    """Record the validated data-row count for one required GTFS table."""

    name: str
    row_count: int


@dataclass(frozen=True)
class GTFSFeedInspection:
    """Summarize one structurally validated GTFS archive without retaining its rows."""

    archive_sha256: str
    tables: tuple[GTFSTableInspection, ...]
    agency_names: tuple[str, ...]
    route_type_counts: tuple[tuple[str, int], ...]
    service_start_date: str | None
    service_end_date: str | None

    def as_dict(self) -> dict[str, object]:
        """Return stable JSON-ready inspection data for a management-command caller."""
        return {
            "archive_sha256": self.archive_sha256,
            "tables": {table.name: table.row_count for table in self.tables},
            "agency_names": list(self.agency_names),
            "route_type_counts": dict(self.route_type_counts),
            "service_start_date": self.service_start_date,
            "service_end_date": self.service_end_date,
        }


def inspect_gtfs_archive(archive_bytes: bytes) -> GTFSFeedInspection:
    """Validate the required CTAN GTFS tables and return a compact content inspection.

    The inspection checks ZIP integrity, one copy of each required root-level table, UTF-8 CSV
    structure, expected columns, complete CSV rows, and core identifiers. It deliberately does
    not yet validate cross-table relationships; that belongs to the later persistent importer.
    """
    if not archive_bytes:
        raise GTFSFeedError("GTFS archive is empty.")
    try:
        archive = ZipFile(BytesIO(archive_bytes))
    except BadZipFile as error:
        raise GTFSFeedError("GTFS source did not contain a valid ZIP archive.") from error
    with archive:
        entries = _required_entries(archive)
        table_inspections: list[GTFSTableInspection] = []
        agency_names: set[str] = set()
        route_type_counts: Counter[str] = Counter()
        service_dates: list[str] = []
        for table_name, required_columns in REQUIRED_TABLE_COLUMNS.items():
            row_count = 0
            for row in _iter_table_rows(archive, entries[table_name], table_name, required_columns):
                _validate_core_values(table_name, row)
                row_count += 1
                if table_name == "agency.txt":
                    agency_names.add(row["agency_name"].strip())
                elif table_name == "routes.txt":
                    route_type_counts[row["route_type"].strip()] += 1
                elif table_name == "calendar.txt":
                    service_dates.extend(
                        (
                            _validate_service_date(row["start_date"], table_name),
                            _validate_service_date(row["end_date"], table_name),
                        )
                    )
                elif table_name == "calendar_dates.txt":
                    service_dates.append(_validate_service_date(row["date"], table_name))
            table_inspections.append(GTFSTableInspection(name=table_name, row_count=row_count))
    return GTFSFeedInspection(
        archive_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        tables=tuple(table_inspections),
        agency_names=tuple(sorted(agency_names)),
        route_type_counts=tuple(sorted(route_type_counts.items())),
        service_start_date=min(service_dates, default=None),
        service_end_date=max(service_dates, default=None),
    )


def _required_entries(archive: ZipFile) -> dict[str, ZipInfo]:
    """Find exactly one root-level archive entry for every table Gadiruta needs."""
    all_entries = [entry for entry in archive.infolist() if not entry.is_dir()]
    if sum(entry.file_size for entry in all_entries) > MAX_UNCOMPRESSED_ARCHIVE_BYTES:
        raise GTFSFeedError("GTFS archive exceeds the uncompressed size limit.")
    entries: dict[str, ZipInfo] = {}
    for table_name in REQUIRED_TABLE_COLUMNS:
        matches = [entry for entry in all_entries if entry.filename == table_name]
        if len(matches) != 1:
            raise GTFSFeedError(f"GTFS archive must contain exactly one {table_name}.")
        entries[table_name] = matches[0]
    return entries


def _iter_table_rows(
    archive: ZipFile,
    entry: ZipInfo,
    table_name: str,
    required_columns: tuple[str, ...],
) -> Iterator[dict[str, str]]:
    """Yield structurally complete CSV rows after validating a table's UTF-8 header and records."""
    try:
        with (
            archive.open(entry) as source,
            TextIOWrapper(source, encoding="utf-8-sig", newline="") as text,
        ):
            # CTAN's published stops include unescaped quotes inside quoted display names.
            # Tolerant parsing preserves their column boundaries; later checks still reject
            # missing headers, incomplete rows, and blank core values.
            reader = csv.DictReader(text, strict=False)
            raw_headers = reader.fieldnames
            if raw_headers is None or any(not header for header in raw_headers):
                raise GTFSFeedError(f"GTFS table {table_name} has no usable header.")
            headers = [header.strip() for header in raw_headers]
            if len(set(headers)) != len(headers):
                raise GTFSFeedError(f"GTFS table {table_name} has duplicate columns.")
            missing_columns = [column for column in required_columns if column not in headers]
            if missing_columns:
                missing = ", ".join(missing_columns)
                raise GTFSFeedError(
                    f"GTFS table {table_name} is missing required columns: {missing}."
                )
            reader.fieldnames = headers
            for line_number, row in enumerate(reader, start=2):
                if not row:
                    continue
                if None in row or any(value is None for value in row.values()):
                    raise GTFSFeedError(
                        f"GTFS table {table_name} has an incomplete row at {line_number}."
                    )
                complete_row = {
                    key: value
                    for key, value in row.items()
                    if key is not None and value is not None
                }
                if not any(value.strip() for value in complete_row.values()):
                    continue
                yield complete_row
    except UnicodeDecodeError as error:
        raise GTFSFeedError(f"GTFS table {table_name} is not valid UTF-8.") from error
    except csv.Error as error:
        raise GTFSFeedError(f"GTFS table {table_name} could not be parsed as CSV.") from error


def _validate_core_values(table_name: str, row: dict[str, str]) -> None:
    """Reject blank identifiers and fields that the first importer/query phases require."""
    required_values = REQUIRED_TABLE_COLUMNS[table_name]
    blank_columns = [column for column in required_values if not row[column].strip()]
    if blank_columns:
        blanks = ", ".join(blank_columns)
        raise GTFSFeedError(f"GTFS table {table_name} has blank required values: {blanks}.")


def _validate_service_date(value: str, table_name: str) -> str:
    """Require GTFS basic-format dates before reporting their overall service range."""
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as error:
        raise GTFSFeedError(
            f"GTFS table {table_name} has an invalid service date: {value!r}."
        ) from error
    return value
