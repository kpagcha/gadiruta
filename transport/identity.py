"""Preserve public place identities while provider records are reconciled."""

from uuid import NAMESPACE_URL, UUID, uuid5

CTAN_POPULATION_CENTRE_PROVIDER_KEY = "ctan:consortium:2:population-centre"


def legacy_public_place_id(provider_key: str, external_id: str) -> UUID | None:
    """Return a former public ID when a known provider record needs compatibility preservation.

    Only the established CTAN Cadiz population-centre namespace has published Gadiruta IDs. New
    provider records return ``None`` so reconciliation can assign a fresh canonical UUID.
    """
    if provider_key != CTAN_POPULATION_CENTRE_PROVIDER_KEY:
        return None
    return uuid5(
        NAMESPACE_URL,
        f"urn:gadiruta:place:ctan:2:population-centre:{external_id}",
    )
