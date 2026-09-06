"""Search a shared, cached catalogue of Cádiz population centres."""

import unicodedata

from django.core.cache import cache
from django.utils import timezone

from transport.domain import Place, PlaceCatalog, PlaceSearchResult
from transport.providers.wiring import get_place_provider

CACHE_KEY = "gadiruta:places:catalog:v2"
CACHE_TTL_SECONDS = 60 * 60


def fold_text(value: str) -> str:
    """Normalize case, accents, and whitespace for catalogue matching and ordering."""
    normalized = unicodedata.normalize("NFKD", value.casefold())
    unaccented = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(unaccented.split())


def get_place_catalog() -> PlaceCatalog:
    """Return a cached Gadiruta snapshot or retrieve normalized places from its provider.

    Successful snapshots, including empty ones, are cached for one hour. Provider failures
    propagate as ProviderError without being cached; expired snapshots are not served as a fallback.
    """
    cached = cache.get(CACHE_KEY)
    if isinstance(cached, PlaceCatalog):
        return cached

    places = get_place_provider().get_places()
    catalog = PlaceCatalog(places=places, fetched_at=timezone.now())
    cache.set(CACHE_KEY, catalog, timeout=CACHE_TTL_SECONDS)
    return catalog


def search_places(query: str, limit: int = 10) -> PlaceSearchResult:
    """Find at most limit centres matching every normalized query token.

    Prefer exact centre names, prefixes, other name matches, then municipality matches.
    Queries shorter than two normalized characters skip catalogue retrieval. Callers must
    validate a positive limit; provider retrieval failures propagate as ProviderError.
    """
    query = fold_text(query)
    if len(query) < 2:
        return PlaceSearchResult(places=(), fetched_at=None)

    catalog = get_place_catalog()
    tokens = query.split()

    def rank(place: Place) -> tuple[int, str, str, str]:
        """Sort by name-match quality, then use labels and public ID as stable tie-breakers."""
        name = fold_text(place.name)
        if name == query:
            score = 0
        elif name.startswith(query):
            score = 1
        elif all(token in name for token in tokens):
            score = 2
        else:
            score = 3
        return score, name, fold_text(place.municipality or ""), str(place.id)

    matches = (
        place
        for place in catalog.places
        if all(token in fold_text(f"{place.name} {place.municipality or ''}") for token in tokens)
    )
    return PlaceSearchResult(
        places=tuple(sorted(matches, key=rank)[:limit]), fetched_at=catalog.fetched_at
    )
