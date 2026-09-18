"""Verify persistent place identities and provider-reference reconciliation."""

from uuid import UUID

import pytest

from transport.domain import ProviderPlace
from transport.models import CanonicalPlace, ProviderPlaceReference
from transport.providers.base import ProviderError
from transport.services.place_identities import reconcile_provider_places

pytestmark = pytest.mark.django_db
CTAN_PROVIDER_KEY = "ctan:consortium:2:population-centre"


def test_first_provider_reference_assigns_a_canonical_uuid() -> None:
    """Assign a new canonical UUID when a provider record has no existing crosswalk."""
    places = reconcile_provider_places(
        CTAN_PROVIDER_KEY,
        (ProviderPlace(external_id="1", name="Cádiz", municipality="Cádiz"),),
    )
    assert UUID(str(places[0].id)).version == 4
    reference = ProviderPlaceReference.objects.get(
        provider_key=CTAN_PROVIDER_KEY,
        external_id="1",
    )
    assert reference.place_id == places[0].id


def test_existing_reference_reuses_identity_and_refreshes_labels() -> None:
    """Keep one public UUID while the active provider updates a place's display labels."""
    first = reconcile_provider_places(
        CTAN_PROVIDER_KEY,
        (ProviderPlace(external_id="1", name="Cádiz", municipality="Cádiz"),),
    )[0]
    second = reconcile_provider_places(
        CTAN_PROVIDER_KEY,
        (ProviderPlace(external_id="1", name="Cádiz centro", municipality=None),),
    )[0]
    assert second.id == first.id
    assert second.name == "Cádiz centro"
    assert second.municipality is None
    assert ProviderPlaceReference.objects.count() == 1
    assert CanonicalPlace.objects.get(pk=first.id).name == "Cádiz centro"


def test_unmapped_provider_records_create_distinct_canonical_places_without_label_matching() -> (
    None
):
    """Avoid conflating same-labelled records from providers that have no explicit crosswalk."""
    first = reconcile_provider_places(
        "future-a",
        (ProviderPlace(external_id="one", name="Centro", municipality="Cádiz"),),
    )[0]
    second = reconcile_provider_places(
        "future-b",
        (ProviderPlace(external_id="two", name="Centro", municipality="Cádiz"),),
    )[0]
    assert first.id != second.id
    assert UUID(str(first.id)).version == 4
    assert UUID(str(second.id)).version == 4
    assert CanonicalPlace.objects.count() == 2
    assert ProviderPlaceReference.objects.count() == 2


def test_duplicate_provider_identifiers_are_unavailable_data() -> None:
    """Reject ambiguous provider catalogues before they can overwrite one canonical reference."""
    with pytest.raises(ProviderError, match="duplicate external identifiers"):
        reconcile_provider_places(
            "future",
            (
                ProviderPlace(external_id="one", name="First", municipality=None),
                ProviderPlace(external_id="one", name="Second", municipality=None),
            ),
        )
