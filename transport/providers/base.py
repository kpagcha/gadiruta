"""Provider-neutral contracts for the transport capabilities currently used by Gadiruta."""

from typing import Protocol

from transport.domain import Place


class ProviderError(Exception):
    """A transport-data provider could not supply usable data for a requested capability."""


class PlaceProvider(Protocol):
    """Supply normalized population centres for the application's place catalogue."""

    def get_places(self) -> tuple[Place, ...]:
        """Return validated places, allowing an empty catalogue, or raise ProviderError.

        Implementations own retrieval, normalization, and resource cleanup. Public IDs must
        remain stable across fetches and label changes. Caching belongs to the application.
        """
        ...
