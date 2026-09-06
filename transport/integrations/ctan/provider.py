"""Implement the place capability with CTAN's verified Cádiz catalogue resources."""

import httpx

from transport.domain import Place
from transport.integrations.ctan.adapters import to_places
from transport.integrations.ctan.client import CTANClient, CTANError
from transport.providers.base import ProviderError


class CTANPlaceProvider:
    """Join CTAN centres and municipality labels behind the normalized place contract."""

    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        """Allow an offline HTTP transport; each catalogue fetch owns and closes its client."""
        self._transport = transport

    def get_places(self) -> tuple[Place, ...]:
        """Fetch normalized places and translate CTAN failures to ProviderError.

        Empty centre lists skip the municipality request. Unusable data from either resource
        fails the whole fetch, while the client continues to tolerate individual bad records.
        """
        try:
            with CTANClient(transport=self._transport) as client:
                centres = client.list_population_centres()
                municipalities = client.list_municipalities() if centres else []
            return to_places(centres, municipalities)
        except CTANError as error:
            raise ProviderError(
                "The place provider could not supply a usable catalogue."
            ) from error
