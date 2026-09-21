"""Build active GTFS stop links from CTAN's population-centre-aware physical-stop catalogue."""

from dataclasses import dataclass

import httpx
from django.db import transaction

from transport.integrations.ctan.adapters import to_places
from transport.integrations.ctan.client import CONSORTIUM_ID, CTANClient, CTANError
from transport.integrations.ctan.provider import CTAN_PLACE_PROVIDER_KEY
from transport.models import GTFSFeedDataset, GTFSPlaceStopLink, GTFSStop
from transport.providers.base import ProviderError
from transport.services.place_identities import reconcile_provider_places


class CTANGTFSLinkError(Exception):
    """CTAN's source catalogues cannot safely refresh active GTFS place-to-stop links."""


@dataclass(frozen=True)
class CTANGTFSLinkRefresh:
    """Summarize the active feed dataset and relationships produced by one CTAN link refresh."""

    dataset_id: int
    place_count: int
    stop_count: int
    link_count: int

    def as_dict(self) -> dict[str, int]:
        """Return stable JSON-ready output for the administrative link-refresh command."""
        return {
            "dataset_id": self.dataset_id,
            "place_count": self.place_count,
            "stop_count": self.stop_count,
            "link_count": self.link_count,
        }


def refresh_active_ctan_gtfs_place_stop_links(
    *, transport: httpx.BaseTransport | None = None
) -> CTANGTFSLinkRefresh:
    """Refresh canonical CTAN places and replace links for the current active GTFS dataset.

    CTAN's `/paradas` catalogue declares each physical stop's `idNucleo`. Its Bahía de Cádiz
    GTFS IDs are verified as `2_<idParada>` for matching records. The refresh rejects an empty
    crosswalk, then replaces only the active dataset's links inside a transaction.
    """
    try:
        with CTANClient(transport=transport) as client:
            centres = client.list_population_centres()
            municipalities = client.list_municipalities() if centres else []
            physical_stops = client.list_physical_stops()
    except CTANError as error:
        raise CTANGTFSLinkError(
            "CTAN could not supply a usable place-to-stop catalogue."
        ) from error
    provider_places = to_places(centres, municipalities)
    try:
        canonical_places = reconcile_provider_places(CTAN_PLACE_PROVIDER_KEY, provider_places)
    except ProviderError as error:
        raise CTANGTFSLinkError(
            "Canonical place identities are temporarily unavailable."
        ) from error
    places_by_centre_id = {
        provider_place.external_id: canonical_place.id
        for provider_place, canonical_place in zip(provider_places, canonical_places, strict=True)
    }
    active_dataset = GTFSFeedDataset.objects.filter(is_active=True).first()
    if active_dataset is None:
        raise CTANGTFSLinkError("No active GTFS dataset is available for place-to-stop linking.")
    source_stop_ids = {
        f"{CONSORTIUM_ID}_{stop.upstream_id}"
        for stop in physical_stops
        if stop.population_centre_id is not None
    }
    gtfs_stop_ids = dict(
        GTFSStop.objects.filter(
            dataset=active_dataset, external_id__in=source_stop_ids
        ).values_list("external_id", "id")
    )
    link_pairs = {
        (
            places_by_centre_id[stop.population_centre_id],
            gtfs_stop_ids[f"{CONSORTIUM_ID}_{stop.upstream_id}"],
        )
        for stop in physical_stops
        if stop.population_centre_id in places_by_centre_id
        and f"{CONSORTIUM_ID}_{stop.upstream_id}" in gtfs_stop_ids
    }
    if not link_pairs:
        raise CTANGTFSLinkError(
            "CTAN stops could not be matched to the active GTFS dataset; existing links were kept."
        )
    with transaction.atomic():
        locked_dataset = (
            GTFSFeedDataset.objects.select_for_update()
            .filter(pk=active_dataset.pk, is_active=True)
            .first()
        )
        if locked_dataset is None:
            raise CTANGTFSLinkError(
                "The active GTFS dataset changed while stop links were refreshed."
            )
        GTFSPlaceStopLink.objects.filter(stop__dataset=locked_dataset).delete()
        GTFSPlaceStopLink.objects.bulk_create(
            [
                GTFSPlaceStopLink(place_id=place_id, stop_id=stop_id)
                for place_id, stop_id in link_pairs
            ]
        )
    return CTANGTFSLinkRefresh(
        dataset_id=active_dataset.pk,
        place_count=len({place_id for place_id, _ in link_pairs}),
        stop_count=len({stop_id for _, stop_id in link_pairs}),
        link_count=len(link_pairs),
    )
