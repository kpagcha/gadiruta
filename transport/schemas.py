"""Public transport response schemas, independent of provider payloads."""

from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from ninja import Field, Schema

from transport.domain import TransportMode


class PlaceResponse(Schema):
    """A population centre available for selection, with stable identity and URL slug."""

    id: UUID = Field(description="Stable Gadiruta place identifier; treat as opaque.")
    slug: str = Field(description="Stable, human-readable Gadiruta place URL key.")
    kind: Literal["population_centre"] = "population_centre"
    name: str
    municipality: str | None


class PlacesResponse(Schema):
    """Matching places and the time their catalogue was fetched."""

    items: list[PlaceResponse]
    fetched_at: datetime | None = Field(
        description="UTC time of the catalogue fetch; null when the query was too short to search."
    )


class PlacesUnavailableResponse(Schema):
    """Report that place search is temporarily unavailable."""

    code: Literal["places_unavailable"] = "places_unavailable"
    message: str = "Place search is temporarily unavailable. Please try again later."


class DirectJourneyResponse(Schema):
    """A direct scheduled service with only timetable details verified by its active provider."""

    line_code: str
    transport_mode: TransportMode = Field(
        description=(
            "Normalized transport category; unknown means the provider could not classify it."
        )
    )
    departure_time: time
    arrival_time: time
    duration_minutes: int = Field(ge=0)
    note: str | None


class DirectJourneysResponse(Schema):
    """A selected direct journey search and its provider-normalized scheduled services."""

    origin: PlaceResponse
    destination: PlaceResponse
    date: date
    depart_after: time | None
    fetched_at: datetime
    warnings: list[Literal["calendar_accuracy_not_guaranteed"]]
    items: list[DirectJourneyResponse]


class JourneyInvalidResponse(Schema):
    """Explain why a direct journey request cannot be searched under the public contract."""

    code: Literal["same_place", "journey_date_unavailable", "journey_place_unsupported"]
    message: str


class JourneyPlaceNotFoundResponse(Schema):
    """Report a canonical place URL slug that does not exist in Gadiruta."""

    code: Literal["journey_place_not_found"] = "journey_place_not_found"
    message: str = "One or both selected places could not be found."


class JourneysUnavailableResponse(Schema):
    """Report a complete direct timetable that the active provider could not supply."""

    code: Literal["journeys_unavailable"] = "journeys_unavailable"
    message: str = "Direct journeys are temporarily unavailable. Please try again later."
