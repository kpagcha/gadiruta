"""Public transport response schemas, independent of CTAN's payloads."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from ninja import Field, Schema


class PlaceResponse(Schema):
    """A population centre available for selection, with its municipality when known."""

    id: UUID = Field(description="Stable Gadiruta place identifier; treat as opaque.")
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
