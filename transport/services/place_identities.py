"""Resolve provider-scoped places into persistent public Gadiruta identities."""

from collections import Counter

from django.db import DatabaseError

from transport.domain import Place, ProviderPlace
from transport.models import CanonicalPlace, ProviderPlaceReference
from transport.providers.base import ProviderError
from transport.services.place_slugs import allocate_place_slug, preferred_place_slug


def reconcile_provider_places(
    provider_key: str, provider_places: tuple[ProviderPlace, ...]
) -> tuple[Place, ...]:
    """Persist provider references and return the corresponding public places in source order.

    Unmapped provider records create fresh canonical places instead of relying on fallible label
    matching. The active provider refreshes display labels for every resolved canonical place.
    """
    external_ids = tuple(place.external_id for place in provider_places)
    if len(external_ids) != len(set(external_ids)):
        raise ProviderError("The place provider returned duplicate external identifiers.")

    try:
        existing_places = list(CanonicalPlace.objects.only("id", "name", "municipality", "slug"))
        occupied_slugs = {place.slug for place in existing_places if place.slug is not None}
        existing_names = {
            preferred_place_slug(place.name, None, disambiguate=False) for place in existing_places
        }
        provider_name_counts = Counter(
            preferred_place_slug(place.name, None, disambiguate=False) for place in provider_places
        )
        references = {
            reference.external_id: reference
            for reference in ProviderPlaceReference.objects.select_related("place").filter(
                provider_key=provider_key, external_id__in=external_ids
            )
        }
        resolved: list[Place] = []
        for provider_place in provider_places:
            reference = references.get(provider_place.external_id)
            canonical_place: CanonicalPlace
            if reference is None:
                name_slug = preferred_place_slug(provider_place.name, None, disambiguate=False)
                preferred_slug = preferred_place_slug(
                    provider_place.name,
                    provider_place.municipality,
                    disambiguate=(
                        provider_name_counts[name_slug] > 1 or name_slug in existing_names
                    ),
                )
                slug = allocate_place_slug(preferred_slug, occupied_slugs)
                canonical_place = CanonicalPlace.objects.create(
                    name=provider_place.name,
                    municipality=provider_place.municipality,
                    slug=slug,
                )
                occupied_slugs.add(slug)
                existing_names.add(name_slug)
                reference, created_reference = ProviderPlaceReference.objects.get_or_create(
                    provider_key=provider_key,
                    external_id=provider_place.external_id,
                    defaults={"place": canonical_place},
                )
                if not created_reference:
                    canonical_place.delete()
                    canonical_place = reference.place
                references[provider_place.external_id] = reference
            else:
                canonical_place = reference.place

            if canonical_place.slug is None:
                name_slug = preferred_place_slug(canonical_place.name, None, disambiguate=False)
                slug = allocate_place_slug(
                    preferred_place_slug(
                        canonical_place.name,
                        canonical_place.municipality,
                        disambiguate=provider_name_counts[name_slug] > 1,
                    ),
                    occupied_slugs,
                )
                canonical_place.slug = slug
                canonical_place.save(update_fields=("slug", "updated_at"))
                occupied_slugs.add(slug)

            if (
                canonical_place.name != provider_place.name
                or canonical_place.municipality != provider_place.municipality
            ):
                canonical_place.name = provider_place.name
                canonical_place.municipality = provider_place.municipality
                canonical_place.save(update_fields=("name", "municipality", "updated_at"))
            resolved.append(
                Place(
                    id=canonical_place.id,
                    name=canonical_place.name,
                    municipality=canonical_place.municipality,
                    slug=canonical_place.slug,
                )
            )
    except DatabaseError as error:
        raise ProviderError("Canonical place identity is temporarily unavailable.") from error
    return tuple(resolved)
