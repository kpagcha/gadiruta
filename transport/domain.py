"""Provider-independent transport values used by application services."""

from dataclasses import dataclass
from datetime import date, datetime, time
from uuid import UUID


@dataclass(frozen=True)
class Place:
    """A searchable population centre with an opaque public ID and normalized display labels."""

    id: UUID
    name: str
    municipality: str | None


@dataclass(frozen=True)
class ProviderPlace:
    """A provider-scoped population centre before Gadiruta resolves public identity."""

    external_id: str
    name: str
    municipality: str | None


@dataclass(frozen=True)
class PlaceCatalog:
    """An immutable location snapshot with the time its provider fetch completed."""

    places: tuple[Place, ...]
    fetched_at: datetime


@dataclass(frozen=True)
class PlaceSearchResult:
    """Ranked matches and their catalogue timestamp, absent when no search was performed."""

    places: tuple[Place, ...]
    fetched_at: datetime | None


@dataclass(frozen=True)
class DirectJourney:
    """One provider-normalized direct scheduled service between two selected places."""

    line_code: str
    departure_time: time
    arrival_time: time
    duration_minutes: int
    note: str | None


@dataclass(frozen=True)
class DirectJourneyCatalog:
    """A complete provider result for one direction and date before optional time filtering."""

    journeys: tuple[DirectJourney, ...]
    fetched_at: datetime


@dataclass(frozen=True)
class DirectJourneySearchResult:
    """A public-place journey search result with its selected date and optional time filter."""

    origin: Place
    destination: Place
    date: date
    depart_after: time | None
    catalog: DirectJourneyCatalog
