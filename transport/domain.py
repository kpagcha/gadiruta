"""Provider-independent transport values used by application services."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Place:
    """A searchable population centre with an opaque public ID and normalized display labels."""

    id: UUID
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
