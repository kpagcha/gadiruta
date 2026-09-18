"""Select concrete capability providers for the current Cádiz application."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from transport.integrations.ctan.provider import CTANDirectJourneyProvider, CTANPlaceProvider
from transport.providers.base import DirectJourneyProvider, PlaceProvider


def validate_place_provider() -> None:
    """Reject an unsupported deployment-selected place provider with a clear startup error."""
    if settings.GADIRUTA_PLACE_PROVIDER != "ctan":
        raise ImproperlyConfigured("GADIRUTA_PLACE_PROVIDER must currently be 'ctan'.")


def get_place_provider() -> PlaceProvider:
    """Select the configured place implementation without exposing it to catalogue consumers."""
    validate_place_provider()
    return CTANPlaceProvider()


def validate_direct_journey_provider() -> None:
    """Reject an unsupported deployment-selected direct journey provider at startup."""
    if settings.GADIRUTA_DIRECT_JOURNEY_PROVIDER != "ctan":
        raise ImproperlyConfigured("GADIRUTA_DIRECT_JOURNEY_PROVIDER must currently be 'ctan'.")


def get_direct_journey_provider() -> DirectJourneyProvider:
    """Select the configured direct journey implementation without exposing it to services."""
    validate_direct_journey_provider()
    return CTANDirectJourneyProvider()
