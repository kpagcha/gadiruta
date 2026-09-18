"""Resolve provider-scoped places into persistent public Gadiruta identities."""

from django.db import DatabaseError

from transport.domain import Place, ProviderPlace
from transport.identity import legacy_public_place_id
from transport.models import CanonicalPlace, ProviderPlaceReference
from transport.providers.base import ProviderError


def reconcile_provider_places(
    provider_key: str, provider_places: tuple[ProviderPlace, ...]
) -> tuple[Place, ...]:
    """Persist provider references and return the corresponding public places in source order.

    Existing CTAN records retain their established UUIDv5 public IDs. Other unmapped provider
    records create a fresh canonical place instead of relying on fallible label matching. The
    active provider refreshes display labels for every resolved canonical place.
    """
    external_ids = tuple(place.external_id for place in provider_places)
    if len(external_ids) != len(set(external_ids)):
        raise ProviderError("The place provider returned duplicate external identifiers.")

    try:
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
                legacy_id = legacy_public_place_id(provider_key, provider_place.external_id)
                if legacy_id is None:
                    canonical_place = CanonicalPlace.objects.create(
                        name=provider_place.name,
                        municipality=provider_place.municipality,
                    )
                    created_canonical_place = True
                else:
                    canonical_place, created_canonical_place = CanonicalPlace.objects.get_or_create(
                        id=legacy_id,
                        defaults={
                            "name": provider_place.name,
                            "municipality": provider_place.municipality,
                        },
                    )
                reference, created_reference = ProviderPlaceReference.objects.get_or_create(
                    provider_key=provider_key,
                    external_id=provider_place.external_id,
                    defaults={"place": canonical_place},
                )
                if not created_reference:
                    if created_canonical_place:
                        canonical_place.delete()
                    canonical_place = reference.place
                references[provider_place.external_id] = reference
            else:
                canonical_place = reference.place

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
                )
            )
    except DatabaseError as error:
        raise ProviderError("Canonical place identity is temporarily unavailable.") from error
    return tuple(resolved)
