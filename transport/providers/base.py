"""Provider-neutral contracts for the transport capabilities currently used by Gadiruta."""

from typing import Protocol

from transport.domain import ProviderPlace


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
