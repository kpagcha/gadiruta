"""Verify environment-based Django configuration and startup validation in isolation."""

import runpy
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

SETTINGS_PATH = Path(__file__).resolve().parents[1] / "gadiruta" / "settings.py"


@pytest.mark.parametrize("secret", [None, "", "   "])
def test_configuration_requires_a_secret_key(
    monkeypatch: pytest.MonkeyPatch, secret: str | None
) -> None:
    """Reject missing or blank secrets instead of starting with an insecure fallback."""
    if secret is None:
        monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("DJANGO_SECRET_KEY", secret)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY must be set"):
        runpy.run_path(str(SETTINGS_PATH))


@pytest.mark.parametrize("debug", [None, "false", " FALSE "])
def test_debug_is_disabled_unless_explicitly_enabled(
    monkeypatch: pytest.MonkeyPatch, debug: str | None
) -> None:
    """Keep debug off when omitted or explicitly disabled, accepting case and whitespace."""
    if debug is None:
        monkeypatch.delenv("DJANGO_DEBUG", raising=False)
    else:
        monkeypatch.setenv("DJANGO_DEBUG", debug)

    assert runpy.run_path(str(SETTINGS_PATH))["DEBUG"] is False


def test_invalid_debug_flag_fails_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject misspelled debug values instead of silently enabling or disabling debug."""
    monkeypatch.setenv("DJANGO_DEBUG", "treu")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_DEBUG must be true or false"):
        runpy.run_path(str(SETTINGS_PATH))


def test_environment_configures_hosts_and_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply host and PostgreSQL environment values while discarding blank host entries."""
    monkeypatch.setenv("DJANGO_DEBUG", "true")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", " example.test, api.example.test, ,")
    monkeypatch.setenv("POSTGRES_DB", "example_db")
    monkeypatch.setenv("POSTGRES_USER", "example_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "example_password")
    monkeypatch.setenv("POSTGRES_HOST", "db.example.test")
    monkeypatch.setenv("POSTGRES_PORT", "5433")

    configuration = runpy.run_path(str(SETTINGS_PATH))

    assert configuration["DEBUG"] is True
    assert configuration["ALLOWED_HOSTS"] == ["example.test", "api.example.test"]
    assert configuration["DATABASES"]["default"] == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "example_db",
        "USER": "example_user",
        "PASSWORD": "example_password",
        "HOST": "db.example.test",
        "PORT": "5433",
        "OPTIONS": {"connect_timeout": 5},
    }
