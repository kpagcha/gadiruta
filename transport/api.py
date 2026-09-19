"""Public place search and direct journey routes."""

import logging
from datetime import date, time

from django.http import HttpRequest
from ninja import Query, Router, Status

from transport.providers.base import ProviderError
from transport.schemas import (
    DirectJourneyResponse,
    DirectJourneysResponse,
    JourneyInvalidResponse,
    JourneyPlaceNotFoundResponse,
    JourneysUnavailableResponse,
    PlaceResponse,
    PlacesResponse,
    PlacesUnavailableResponse,
)
from transport.services.journeys import (
    JourneyDateUnavailableError,
    JourneyPlaceNotFoundError,
    JourneyPlaceUnsupportedError,
    search_direct_journeys,
)
from transport.services.places import search_places

router = Router(tags=["Places"])
logger = logging.getLogger(__name__)


@router.get("/places", response={200: PlacesResponse, 503: PlacesUnavailableResponse})
def places(
    request: HttpRequest,
    q: str = Query(
        "", max_length=100, description="Population-centre or municipality search text."
    ),
    limit: int = Query(10, ge=1, le=50),
) -> PlacesResponse | Status[PlacesUnavailableResponse]:
    """Search Cádiz population centres by name or municipality, ignoring case and accents.

    Queries with fewer than two normalized characters return no items without searching.
    Results prefer exact and prefix name matches, then other name and municipality matches.
    The provider catalogue is cached for one hour; an unavailable or unusable provider response
    returns 503 when the cache cannot serve the request. Physical stops are not included yet.
    """
    try:
        result = search_places(q, limit)
    except ProviderError:
        logger.warning("The place provider could not supply the catalogue.")
        return Status(503, PlacesUnavailableResponse())
    return PlacesResponse(
        items=[
            PlaceResponse(
                id=place.id,
                slug=place.slug,
                name=place.name,
                municipality=place.municipality,
            )
            for place in result.places
        ],
        fetched_at=result.fetched_at,
    )


@router.get(
    "/journeys/direct",
    response={
        200: DirectJourneysResponse,
        404: JourneyPlaceNotFoundResponse,
        422: JourneyInvalidResponse,
        503: JourneysUnavailableResponse,
    },
    tags=["Journeys"],
)
def direct_journeys(
    request: HttpRequest,
    origin: str = Query(..., min_length=1, max_length=255),
    destination: str = Query(..., min_length=1, max_length=255),
    journey_date: date = Query(alias="date"),  # noqa: B008
    depart_after: time | None = Query(None),  # noqa: B008
    depart_before: time | None = Query(  # noqa: B008
        None,
        description="Return all selected-day services before this exclusive departure-time cutoff.",
    ),
) -> (
    DirectJourneysResponse
    | Status[JourneyPlaceNotFoundResponse]
    | Status[JourneyInvalidResponse]
    | Status[JourneysUnavailableResponse]
):
    """Find scheduled direct services for two selected population centres on one supported date.

    `origin` and `destination` must be stable Gadiruta place slugs returned by place search.
    Gadiruta does not calculate transfers. CTAN has no reliable year parameter and has returned
    working-day schedules for observed holidays, so dates are limited to the current local year
    and every response warns that calendar accuracy is not guaranteed. `depart_before` returns the
    chronologically ordered selected-day services before its exclusive time cutoff; clients can
    page that complete earlier segment locally.
    """
    try:
        result = search_direct_journeys(
            origin, destination, journey_date, depart_after, depart_before
        )
    except ValueError:
        return Status(
            422,
            JourneyInvalidResponse(
                code="same_place", message="Origin and destination must be different places."
            ),
        )
    except JourneyDateUnavailableError:
        return Status(
            422,
            JourneyInvalidResponse(
                code="journey_date_unavailable",
                message="Direct journey dates must be today through the end of the current year.",
            ),
        )
    except JourneyPlaceNotFoundError:
        return Status(404, JourneyPlaceNotFoundResponse())
    except JourneyPlaceUnsupportedError:
        return Status(
            422,
            JourneyInvalidResponse(
                code="journey_place_unsupported",
                message="One or both selected places are unavailable for direct journey search.",
            ),
        )
    except ProviderError:
        logger.warning("The direct journey provider could not supply a complete timetable.")
        return Status(503, JourneysUnavailableResponse())
    return DirectJourneysResponse(
        origin=PlaceResponse(
            id=result.origin.id,
            slug=result.origin.slug,
            name=result.origin.name,
            municipality=result.origin.municipality,
        ),
        destination=PlaceResponse(
            id=result.destination.id,
            slug=result.destination.slug,
            name=result.destination.name,
            municipality=result.destination.municipality,
        ),
        date=result.date,
        depart_after=result.depart_after,
        depart_before=result.depart_before,
        has_earlier_departures=result.has_earlier_departures,
        fetched_at=result.catalog.fetched_at,
        warnings=["calendar_accuracy_not_guaranteed"],
        items=[
            DirectJourneyResponse(
                line_code=journey.line_code,
                transport_mode=journey.transport_mode,
                departure_time=journey.departure_time,
                arrival_time=journey.arrival_time,
                duration_minutes=journey.duration_minutes,
                note=journey.note,
            )
            for journey in result.catalog.journeys
        ],
    )
