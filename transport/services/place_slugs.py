"""Allocate human-readable, stable URL slugs for canonical population centres."""

from collections.abc import Collection

from django.utils.text import slugify

MAX_SLUG_LENGTH = 255


def preferred_place_slug(name: str, municipality: str | None, *, disambiguate: bool) -> str:
    """Build a readable base slug, adding municipality context when the name is not unique.

    The caller decides whether a name collides in its current catalogue batch. The returned value
    may still collide with an existing canonical record and must be passed to `allocate_place_slug`.
    """
    place_name = slugify(name) or "place"
    municipality_name = slugify(municipality or "")
    if disambiguate and municipality_name:
        return _bounded_slug(f"{place_name}-{municipality_name}")
    return _bounded_slug(place_name)


def allocate_place_slug(preferred: str, occupied: Collection[str]) -> str:
    """Return an unused stable slug, adding a minimal numeric suffix only when required."""
    occupied_slugs = set(occupied)
    if preferred not in occupied_slugs:
        return preferred
    suffix_number = 2
    while True:
        suffix = f"-{suffix_number}"
        candidate = f"{preferred[: MAX_SLUG_LENGTH - len(suffix)]}{suffix}"
        if candidate not in occupied_slugs:
            return candidate
        suffix_number += 1


def _bounded_slug(value: str) -> str:
    """Keep generated slugs within the persisted field's maximum length without producing blanks."""
    return value[:MAX_SLUG_LENGTH] or "place"
