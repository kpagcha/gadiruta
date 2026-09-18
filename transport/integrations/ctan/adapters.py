"""Translate verified CTAN population centres into provider-scoped place records."""

from transport.domain import ProviderPlace
from transport.integrations.ctan.schemas import Municipality, PopulationCentre


def to_places(
    centres: list[PopulationCentre], municipalities: list[Municipality]
) -> tuple[ProviderPlace, ...]:
    """Join municipality names while keeping CTAN references inside the provider boundary.

    Missing municipality relationships yield an unknown label rather than dropping a usable centre.
    Canonical public identity is resolved by the application after this adapter returns.
    """
    names = {municipality.upstream_id: municipality.name for municipality in municipalities}
    return tuple(
        ProviderPlace(
            external_id=centre.upstream_id,
            name=centre.name,
            municipality=names.get(centre.municipality_id) if centre.municipality_id else None,
        )
        for centre in centres
    )
