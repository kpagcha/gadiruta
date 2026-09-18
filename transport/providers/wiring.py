"""Select concrete capability providers for the current Cádiz application."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from transport.integrations.ctan.provider import CTANPlaceProvider
from transport.providers.base import PlaceProvider


def validate_place_provider() -> None:
    """Reject an unsupported deployment-selected place provider with a clear startup error."""
    if settings.GADIRUTA_PLACE_PROVIDER != "ctan":
        raise ImproperlyConfigured("GADIRUTA_PLACE_PROVIDER must currently be 'ctan'.")


def get_place_provider() -> PlaceProvider:
    """Select the configured place implementation without exposing it to catalogue consumers."""
    validate_place_provider()
    return CTANPlaceProvider()
