"""Persist canonical place identities independently of transport-provider identifiers."""

import uuid

from django.db import models
from django.db.models import Q


class CanonicalPlace(models.Model):
    """Store Gadiruta's stable public identity and current display labels for one place."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=32, default="population_centre", editable=False)
    name = models.CharField(max_length=200)
    municipality = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Keep place presentation ordering stable for administrative inspection."""

        ordering = ("kind", "name", "id")


class ProviderPlaceReference(models.Model):
    """Map one provider-scoped external place identifier to a canonical Gadiruta place."""

    provider_key = models.CharField(max_length=120)
    external_id = models.CharField(max_length=255)
    place = models.ForeignKey(CanonicalPlace, on_delete=models.CASCADE, related_name="references")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Require each external identifier to map to exactly one canonical place per provider."""

        constraints = [
            models.UniqueConstraint(
                fields=("provider_key", "external_id"),
                name="transport_provider_place_reference_unique",
            )
        ]


class GTFSFeedDataset(models.Model):
    """Record one immutable, validated GTFS import and whether it serves current queries."""

    source_url = models.URLField(max_length=500)
    archive_sha256 = models.CharField(max_length=64, unique=True)
    service_start_date = models.DateField(null=True, blank=True)
    service_end_date = models.DateField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        """Allow historical datasets while ensuring only one can serve live queries."""

        constraints = [
            models.UniqueConstraint(
                fields=("is_active",),
                condition=Q(is_active=True),
                name="transport_gtfs_one_active_dataset",
            )
        ]
        ordering = ("-imported_at",)


class GTFSAgency(models.Model):
    """Store one feed-scoped GTFS agency/operator record."""

    dataset = models.ForeignKey(GTFSFeedDataset, on_delete=models.CASCADE, related_name="agencies")
    external_id = models.CharField(max_length=255)
    name = models.CharField(max_length=300)
    url = models.URLField(max_length=500)
    timezone = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=20, blank=True)
    fare_url = models.URLField(max_length=500, blank=True)

    class Meta:
        """Keep each source agency ID unique within its immutable dataset."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "external_id"),
                name="transport_gtfs_agency_dataset_external_id_unique",
            )
        ]


class GTFSStop(models.Model):
    """Store one feed-scoped physical stop with its provided geographic coordinates."""

    dataset = models.ForeignKey(GTFSFeedDataset, on_delete=models.CASCADE, related_name="stops")
    external_id = models.CharField(max_length=255)
    name = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        """Keep source stops unique within a dataset and index geographic import inspection."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "external_id"),
                name="transport_gtfs_stop_dataset_external_id_unique",
            )
        ]


class GTFSRoute(models.Model):
    """Store one feed-scoped route/line and its normalized GTFS mode code."""

    dataset = models.ForeignKey(GTFSFeedDataset, on_delete=models.CASCADE, related_name="routes")
    agency = models.ForeignKey(GTFSAgency, on_delete=models.PROTECT, related_name="routes")
    external_id = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100)
    long_name = models.CharField(max_length=500)
    route_type = models.IntegerField()
    url = models.URLField(max_length=500, blank=True)
    color = models.CharField(max_length=20, blank=True)
    text_color = models.CharField(max_length=20, blank=True)

    class Meta:
        """Keep route IDs unique and support the active-dataset route lookup path."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "external_id"),
                name="transport_gtfs_route_dataset_external_id_unique",
            )
        ]
        indexes = [models.Index(fields=("dataset", "route_type"))]


class GTFSTrip(models.Model):
    """Store one dated-service candidate trip before its ordered stop-time records."""

    dataset = models.ForeignKey(GTFSFeedDataset, on_delete=models.CASCADE, related_name="trips")
    route = models.ForeignKey(GTFSRoute, on_delete=models.CASCADE, related_name="trips")
    external_id = models.CharField(max_length=255)
    service_id = models.CharField(max_length=255)
    headsign = models.CharField(max_length=500, blank=True)
    direction_id = models.IntegerField(null=True, blank=True)
    shape_external_id = models.CharField(max_length=255, blank=True)

    class Meta:
        """Keep feed-wide trip identities and index service-date candidate resolution."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "external_id"),
                name="transport_gtfs_trip_dataset_external_id_unique",
            )
        ]
        indexes = [models.Index(fields=("dataset", "service_id"))]


class GTFSStopTime(models.Model):
    """Store one ordered stop call with GTFS seconds-from-service-day time values."""

    trip = models.ForeignKey(GTFSTrip, on_delete=models.CASCADE, related_name="stop_times")
    stop = models.ForeignKey(GTFSStop, on_delete=models.PROTECT, related_name="stop_times")
    arrival_seconds = models.PositiveIntegerField()
    departure_seconds = models.PositiveIntegerField()
    sequence = models.PositiveIntegerField()
    pickup_type = models.PositiveSmallIntegerField(null=True, blank=True)
    drop_off_type = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        """Preserve call order and optimize direct matching by stop and trip sequence."""

        constraints = [
            models.UniqueConstraint(
                fields=("trip", "sequence"),
                name="transport_gtfs_stop_time_trip_sequence_unique",
            )
        ]
        indexes = [models.Index(fields=("stop", "trip", "sequence"))]


class GTFSCalendarService(models.Model):
    """Store one regular weekly service calendar with its inclusive validity range."""

    dataset = models.ForeignKey(GTFSFeedDataset, on_delete=models.CASCADE, related_name="calendars")
    service_id = models.CharField(max_length=255)
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        """Keep each service calendar unique for date-specific direct-journey filtering."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "service_id"),
                name="transport_gtfs_calendar_dataset_service_id_unique",
            )
        ]


class GTFSCalendarException(models.Model):
    """Store one addition or removal overriding the regular service calendar on a date."""

    dataset = models.ForeignKey(
        GTFSFeedDataset, on_delete=models.CASCADE, related_name="exceptions"
    )
    service_id = models.CharField(max_length=255)
    date = models.DateField()
    exception_type = models.PositiveSmallIntegerField()

    class Meta:
        """Keep one source exception per service date and support direct-date resolution."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "service_id", "date"),
                name="transport_gtfs_exception_dataset_service_date_unique",
            )
        ]
        indexes = [models.Index(fields=("dataset", "date", "service_id"))]


class GTFSShapePoint(models.Model):
    """Store one ordered geographic shape point for a feed-scoped route pattern."""

    dataset = models.ForeignKey(
        GTFSFeedDataset, on_delete=models.CASCADE, related_name="shape_points"
    )
    shape_external_id = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    sequence = models.PositiveIntegerField()

    class Meta:
        """Keep shape points ordered and unique for future route-geometry rendering."""

        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "shape_external_id", "sequence"),
                name="transport_gtfs_shape_dataset_id_sequence_unique",
            )
        ]


class GTFSPlaceStopLink(models.Model):
    """Associate one user-facing place with a physical stop in a particular GTFS dataset."""

    place = models.ForeignKey(
        CanonicalPlace, on_delete=models.CASCADE, related_name="gtfs_stop_links"
    )
    stop = models.ForeignKey(GTFSStop, on_delete=models.CASCADE, related_name="place_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Prevent duplicate place-stop associations while allowing many stops per place."""

        constraints = [
            models.UniqueConstraint(
                fields=("place", "stop"),
                name="transport_gtfs_place_stop_link_unique",
            )
        ]
