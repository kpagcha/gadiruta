"""Verify the GTFS persistence schema's essential identities and direct-query indexes."""

from django.db import models

from transport.models import (
    GTFSCalendarException,
    GTFSCalendarService,
    GTFSFeedDataset,
    GTFSRoute,
    GTFSStop,
    GTFSStopTime,
    GTFSTrip,
)


def constraint_names(model: type[models.Model]) -> set[str]:
    """Return the named database constraints declared by one Django model class."""
    return {
        constraint.name for constraint in model._meta.constraints if constraint.name is not None
    }


def index_fields(model: type[models.Model]) -> set[tuple[str, ...]]:
    """Return declared index field tuples without connecting to the configured database."""
    return {tuple(index.fields) for index in model._meta.indexes}


def test_gtfs_schema_preserves_feed_scoped_identities_and_lookup_indexes() -> None:
    """Protect the keys needed for immutable imports and future direct-service matching."""
    assert "transport_gtfs_one_active_dataset" in constraint_names(GTFSFeedDataset)
    assert "transport_gtfs_stop_dataset_external_id_unique" in constraint_names(GTFSStop)
    assert "transport_gtfs_trip_dataset_external_id_unique" in constraint_names(GTFSTrip)
    assert "transport_gtfs_calendar_dataset_service_id_unique" in constraint_names(
        GTFSCalendarService
    )
    assert "transport_gtfs_exception_dataset_service_date_unique" in constraint_names(
        GTFSCalendarException
    )
    assert "transport_gtfs_stop_time_trip_sequence_unique" in constraint_names(GTFSStopTime)
    assert ("dataset", "route_type") in index_fields(GTFSRoute)
    assert ("dataset", "service_id") in index_fields(GTFSTrip)
    assert ("stop", "trip", "sequence") in index_fields(GTFSStopTime)
