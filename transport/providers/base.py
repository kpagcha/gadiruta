"""Provider-neutral contracts for the transport capabilities currently used by Gadiruta."""

from datetime import date
from typing import Protocol

from transport.domain import DirectJourney, ProviderPlace


class ProviderError(Exception):
    """A transport-data provider could not supply usable data for a requested capability."""


class PlaceProvider(Protocol):
    """Supply provider-scoped population centres for the application's place catalogue."""

    provider_key: str

    def get_places(self) -> tuple[ProviderPlace, ...]:
        """Return validated provider places, allowing an empty catalogue, or raise ProviderError.

        Implementations own retrieval, normalization, provider IDs, and resource cleanup. Public
        Gadiruta identity and caching belong to the application.
        """
        ...


class DirectJourneyProvider(Protocol):
    """Supply normalized direct scheduled services for two provider-scoped population centres."""

    provider_key: str

    def get_direct_journeys(
        self, origin: ProviderPlace, destination: ProviderPlace, journey_date: date
    ) -> tuple[DirectJourney, ...]:
        """Return complete direct services for one date or raise ProviderError.

        Implementations own provider-specific discovery, timetable retrieval, and normalization.
        The application owns public identity, cache policy, optional departure filtering, and API
        behavior.
        """
        ...
