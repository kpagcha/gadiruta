"""Select concrete capability providers for the current Cádiz application."""

from transport.integrations.ctan.provider import CTANPlaceProvider
from transport.providers.base import PlaceProvider


def get_place_provider() -> PlaceProvider:
    """Select the CTAN implementation without exposing it to catalogue consumers."""
    return CTANPlaceProvider()
