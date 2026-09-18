"""Django application configuration for persisted transport identities."""

from django.apps import AppConfig


class TransportConfig(AppConfig):
    """Register transport models and validate configured provider selection at startup."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "transport"

    def ready(self) -> None:
        """Validate the active place-provider setting after Django settings are available."""
        from transport.providers.wiring import validate_place_provider

        validate_place_provider()
