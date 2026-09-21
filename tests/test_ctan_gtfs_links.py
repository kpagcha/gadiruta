"""Verify the CTAN-backed crosswalk between canonical places and active GTFS stops."""

from pathlib import Path

import httpx
import pytest

from transport.models import CanonicalPlace, GTFSFeedDataset, GTFSPlaceStopLink, GTFSStop
from transport.services.ctan_gtfs_links import (
    CTANGTFSLinkError,
    refresh_active_ctan_gtfs_place_stop_links,
)


def ctan_catalogue_transport(ctan_fixture_dir: Path) -> httpx.MockTransport:
    """Serve captured centres, municipalities, and physical stops to an offline link refresh."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Map each expected CTAN catalogue path to its saved representative response."""
        filenames = {
            "/v1/Consorcios/2/nucleos": "nucleos.json",
            "/v1/Consorcios/2/municipios/": "municipios.json",
            "/v1/Consorcios/2/paradas": "paradas_sample.json",
        }
        return httpx.Response(
            200, content=(ctan_fixture_dir / filenames[request.url.path]).read_bytes()
        )

    return httpx.MockTransport(respond)


@pytest.mark.django_db
def test_refresh_links_current_ctan_places_to_matching_active_gtfs_stops(
    ctan_fixture_dir: Path,
) -> None:
    """Use verified CTAN source IDs rather than names to create one current-dataset crosswalk."""
    dataset = GTFSFeedDataset.objects.create(
        source_url="https://example.invalid/gtfs.zip",
        archive_sha256="1" * 64,
        is_active=True,
    )
    for external_id in ("2_73", "2_91", "2_155", "2_173", "2_stale"):
        GTFSStop.objects.create(
            dataset=dataset,
            external_id=external_id,
            name=external_id,
            latitude=36.0,
            longitude=-6.0,
        )

    result = refresh_active_ctan_gtfs_place_stop_links(
        transport=ctan_catalogue_transport(ctan_fixture_dir)
    )
    assert result.dataset_id == dataset.pk
    assert result.place_count == result.stop_count == result.link_count == 4
    assert set(
        GTFSPlaceStopLink.objects.filter(stop__dataset=dataset).values_list(
            "stop__external_id", flat=True
        )
    ) == {"2_73", "2_91", "2_155", "2_173"}


@pytest.mark.django_db
def test_no_matches_keep_existing_active_dataset_links(ctan_fixture_dir: Path) -> None:
    """Avoid replacing a known crosswalk with an empty result from incompatible source datasets."""
    dataset = GTFSFeedDataset.objects.create(
        source_url="https://example.invalid/gtfs.zip",
        archive_sha256="2" * 64,
        is_active=True,
    )
    stop = GTFSStop.objects.create(
        dataset=dataset,
        external_id="2_unmatched",
        name="Unmatched",
        latitude=36.0,
        longitude=-6.0,
    )
    place = CanonicalPlace.objects.create(name="Existing", slug="existing")
    GTFSPlaceStopLink.objects.create(place=place, stop=stop)
    with pytest.raises(CTANGTFSLinkError, match="could not be matched"):
        refresh_active_ctan_gtfs_place_stop_links(
            transport=ctan_catalogue_transport(ctan_fixture_dir)
        )
    assert GTFSPlaceStopLink.objects.filter(stop__dataset=dataset).count() == 1
