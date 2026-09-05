"""Translate verified CTAN population centres into Gadiruta places."""

from uuid import NAMESPACE_URL, uuid5

from transport.domain import Place
from transport.integrations.ctan.client import CONSORTIUM_ID
from transport.integrations.ctan.schemas import Municipality, PopulationCentre


def to_places(
    centres: list[PopulationCentre], municipalities: list[Municipality]
) -> tuple[Place, ...]:
    """Join municipality names and assign stable public IDs while retaining provider references.

    Missing municipality relationships yield an unknown label rather than dropping the centre.
    Public identity depends only on the scoped provider ID, not labels or record order.
    """
    names = {municipality.upstream_id: municipality.name for municipality in municipalities}
    return tuple(
        Place(
            # This stable identity must survive cache refreshes and future persistence.
            id=uuid5(
                NAMESPACE_URL,
                f"urn:gadiruta:place:ctan:{CONSORTIUM_ID}:population-centre:{centre.upstream_id}",
            ),
            name=centre.name,
            municipality=names.get(centre.municipality_id) if centre.municipality_id else None,
            provider="ctan",
            consortium_id=CONSORTIUM_ID,
            upstream_id=centre.upstream_id,
            upstream_municipality_id=centre.municipality_id,
            upstream_zone=centre.zone,
        )
        for centre in centres
    )
