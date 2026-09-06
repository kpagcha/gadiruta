"""Public place search routes."""

import logging

from django.http import HttpRequest
from ninja import Query, Router, Status

from transport.providers.base import ProviderError
from transport.schemas import PlaceResponse, PlacesResponse, PlacesUnavailableResponse
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
            PlaceResponse(id=place.id, name=place.name, municipality=place.municipality)
            for place in result.places
        ],
        fetched_at=result.fetched_at,
    )
