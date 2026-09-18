"""Resolve public places and retrieve cached direct journeys from the active provider."""

from datetime import date, time

from django.core.cache import cache
from django.db import DatabaseError
from django.utils import timezone

from transport.domain import (
    DirectJourneyCatalog,
    DirectJourneySearchResult,
    Place,
    ProviderPlace,
)
from transport.models import CanonicalPlace, ProviderPlaceReference
from transport.providers.base import ProviderError
from transport.providers.wiring import get_direct_journey_provider

CACHE_TTL_SECONDS = 60 * 60
EARLIER_DEPARTURE_PAGE_SIZE = 4


class JourneyPlaceNotFoundError(Exception):
    """A requested canonical public place ID is not present in the local identity store."""


class JourneyPlaceUnsupportedError(Exception):
    """A known canonical place has no reference for the active direct journey provider."""


class JourneyDateUnavailableError(Exception):
    """A requested date lies outside CTAN's reliable current-year search window."""


def search_direct_journeys(
    origin_slug: str,
    destination_slug: str,
    journey_date: date,
    depart_after: time | None = None,
    depart_before: time | None = None,
) -> DirectJourneySearchResult:
    """Return direct services filtered by optional departure bounds and an earlier-page cursor.

    The active provider owns its upstream date interpretation. Gadiruta limits requests to today's
    date through the end of the current Europe/Madrid calendar year because CTAN exposes no
    reliable year parameter and misclassifies observed holidays. A ``depart_before`` cursor returns
    only the preceding page, ordered chronologically, while the unbounded response stays complete
    for the existing later-results UI.
    """
    _validate_journey_date(journey_date)
    provider = get_direct_journey_provider()
    public_origin, public_destination = _resolve_public_places(origin_slug, destination_slug)
    if public_origin.id == public_destination.id:
        raise ValueError("Origin and destination must differ.")
    origin, destination = _resolve_provider_places(
        provider.provider_key, public_origin, public_destination
    )
    cache_key = _cache_key(
        provider.provider_key, origin.external_id, destination.external_id, journey_date
    )
    cached = cache.get(cache_key)
    if isinstance(cached, DirectJourneyCatalog):
        catalog = cached
    else:
        catalog = DirectJourneyCatalog(
            journeys=provider.get_direct_journeys(origin, destination, journey_date),
            fetched_at=timezone.now(),
        )
        cache.set(cache_key, catalog, timeout=CACHE_TTL_SECONDS)
    all_journeys = tuple(
        sorted(
            catalog.journeys,
            key=lambda journey: (
                journey.departure_time,
                journey.arrival_time,
                journey.line_code,
                journey.note or "",
            ),
        )
    )
    filtered_journeys = tuple(
        journey
        for journey in all_journeys
        if (depart_after is None or journey.departure_time >= depart_after)
        and (depart_before is None or journey.departure_time < depart_before)
    )
    if depart_before is None:
        journeys = filtered_journeys
        has_earlier_departures = bool(
            journeys
            and any(journey.departure_time < journeys[0].departure_time for journey in all_journeys)
        )
    else:
        journeys = filtered_journeys[-EARLIER_DEPARTURE_PAGE_SIZE:]
        has_earlier_departures = len(filtered_journeys) > len(journeys)
    return DirectJourneySearchResult(
        origin=public_origin,
        destination=public_destination,
        date=journey_date,
        depart_after=depart_after,
        depart_before=depart_before,
        has_earlier_departures=has_earlier_departures,
        catalog=DirectJourneyCatalog(journeys=journeys, fetched_at=catalog.fetched_at),
    )


def _validate_journey_date(journey_date: date) -> None:
    """Allow only today's date through the current local calendar year's final day."""
    today = timezone.localdate()
    if journey_date < today or journey_date.year != today.year:
        raise JourneyDateUnavailableError


def _resolve_provider_places(
    provider_key: str, origin: Place, destination: Place
) -> tuple[ProviderPlace, ProviderPlace]:
    """Map two public places to active-provider IDs while distinguishing missing and unsupported."""
    try:
        references = {
            reference.place_id: reference
            for reference in ProviderPlaceReference.objects.filter(
                provider_key=provider_key, place_id__in=(origin.id, destination.id)
            ).select_related("place")
        }
    except DatabaseError as error:
        raise ProviderError("Canonical place identity is temporarily unavailable.") from error
    if origin.id not in references or destination.id not in references:
        raise JourneyPlaceUnsupportedError
    return (
        ProviderPlace(
            external_id=references[origin.id].external_id,
            name=origin.name,
            municipality=origin.municipality,
        ),
        ProviderPlace(
            external_id=references[destination.id].external_id,
            name=destination.name,
            municipality=destination.municipality,
        ),
    )


def _resolve_public_places(origin_slug: str, destination_slug: str) -> tuple[Place, Place]:
    """Load two canonical places by stable URL slug or distinguish missing provider support gaps."""
    try:
        places = CanonicalPlace.objects.in_bulk((origin_slug, destination_slug), field_name="slug")
    except DatabaseError as error:
        raise ProviderError("Canonical place identity is temporarily unavailable.") from error
    if origin_slug not in places or destination_slug not in places:
        raise JourneyPlaceNotFoundError
    return (
        _to_place(places[origin_slug]),
        _to_place(places[destination_slug]),
    )


def _to_place(place: CanonicalPlace) -> Place:
    """Expose only the canonical public fields needed by direct journey services."""
    if place.slug is None:
        raise ProviderError("Canonical place identity is temporarily unavailable.")
    return Place(id=place.id, slug=place.slug, name=place.name, municipality=place.municipality)


def _cache_key(provider_key: str, origin_id: str, destination_id: str, journey_date: date) -> str:
    """Name one complete upstream timetable independently of public IDs and time filtering."""
    return (
        f"gadiruta:journeys:direct:v1:{provider_key}:{origin_id}:"
        f"{destination_id}:{journey_date.isoformat()}"
    )
