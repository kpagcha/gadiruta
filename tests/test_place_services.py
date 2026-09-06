"""Verify catalogue services and API behavior independently of concrete integrations."""

from dataclasses import dataclass
from uuid import UUID

import pytest
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from transport.domain import Place
from transport.providers.base import PlaceProvider, ProviderError
from transport.services import places as service


@dataclass
class StubPlaceProvider:
    """Supply normalized test locations or a failure while counting catalogue fetches."""

    places: tuple[Place, ...]
    error: Exception | None = None
    calls: int = 0

    def get_places(self) -> tuple[Place, ...]:
        """Return the configured snapshot or raise the selected failure without using HTTP."""
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.places


@pytest.fixture
def place_provider(monkeypatch: pytest.MonkeyPatch) -> StubPlaceProvider:
    """Replace provider selection with a structural implementation of only the place capability."""
    provider = StubPlaceProvider(
        places=(
            Place(id=UUID(int=1), name="Centro", municipality="Bahía"),
            Place(id=UUID(int=2), name="Bahía", municipality=None),
        )
    )

    def select_provider() -> PlaceProvider:
        """Supply a provider satisfying the protocol without inheriting an integration class."""
        return provider

    monkeypatch.setattr(service, "get_place_provider", select_provider)
    return provider


def test_search_ranks_and_caches_normalized_provider_places(
    place_provider: StubPlaceProvider,
) -> None:
    """Search and reuse a complete Gadiruta snapshot without provider IDs or parsing knowledge."""
    first = service.search_places("  BAHIA  ", limit=1)
    assert first.places == (place_provider.places[1],)
    assert first.fetched_at is not None
    assert timezone.is_aware(first.fetched_at)
    second = service.search_places("bahía")
    assert second.places == tuple(reversed(place_provider.places))
    assert second.fetched_at == first.fetched_at
    assert place_provider.calls == 1


def test_api_accepts_a_provider_without_upstream_metadata(
    client: Client, place_provider: StubPlaceProvider
) -> None:
    """Return the unchanged public schema for normalized locations from another implementation."""
    response = client.get("/api/v1/places", {"q": "bahia centro"})
    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": str(place_provider.places[0].id),
            "kind": "population_centre",
            "name": "Centro",
            "municipality": "Bahía",
        }
    ]
    assert response.json()["fetched_at"] is not None


def test_provider_error_is_safe_and_recoverable(
    client: Client, place_provider: StubPlaceProvider, caplog: pytest.LogCaptureFixture
) -> None:
    """Handle neutral failures with the existing 503 contract without caching or leaking details."""
    place_provider.error = ProviderError("Private supplier details")
    response = client.get("/api/v1/places", {"q": "bahia"})
    assert response.status_code == 503
    assert response.json() == {
        "code": "places_unavailable",
        "message": "Place search is temporarily unavailable. Please try again later.",
    }
    assert cache.get(service.CACHE_KEY) is None
    assert "Private supplier details" not in caplog.text
    assert "The place provider could not supply the catalogue." in caplog.text
    place_provider.error = None
    assert client.get("/api/v1/places", {"q": "bahia"}).status_code == 200
    assert place_provider.calls == 2


def test_empty_provider_catalogue_is_a_cacheable_success(place_provider: StubPlaceProvider) -> None:
    """Cache a valid empty snapshot with its timestamp instead of treating it as a failure."""
    place_provider.places = ()
    first = service.get_place_catalog()
    second = service.get_place_catalog()
    assert first.places == ()
    assert timezone.is_aware(first.fetched_at)
    assert second == first
    assert place_provider.calls == 1


def test_short_query_skips_provider_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid even constructing a provider when the normalized query cannot trigger a search."""

    def reject_selection() -> PlaceProvider:
        """Fail if a short query reaches the provider composition boundary."""
        raise AssertionError("A short query must not select a provider.")

    monkeypatch.setattr(service, "get_place_provider", reject_selection)
    result = service.search_places(" á ")
    assert result.places == ()
    assert result.fetched_at is None


def test_unexpected_provider_errors_are_not_swallowed(place_provider: StubPlaceProvider) -> None:
    """Propagate programming errors so they cannot silently become cached empty catalogues."""
    place_provider.error = RuntimeError("Unexpected implementation failure")
    with pytest.raises(RuntimeError, match="Unexpected implementation failure"):
        service.get_place_catalog()
    assert cache.get(service.CACHE_KEY) is None
