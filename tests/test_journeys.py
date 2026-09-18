"""Exercise direct-journey service and API behavior through a provider-neutral test double."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, time
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from transport.domain import DirectJourney, ProviderPlace
from transport.models import CanonicalPlace, ProviderPlaceReference
from transport.providers.base import DirectJourneyProvider, ProviderError
from transport.services import journeys as service


@dataclass
class StubDirectJourneyProvider:
    """Return configured normalized services while recording retrievals and provider errors."""

    provider_key: str = "stub-direct"
    journeys: tuple[DirectJourney, ...] = (
        DirectJourney("M-1", time(9, 0), time(9, 35), 35, None),
        DirectJourney("M-2", time(10, 0), time(10, 20), 20, "Limited service"),
    )
    error: Exception | None = None
    calls: list[tuple[ProviderPlace, ProviderPlace, date]] = field(default_factory=list)

    def get_direct_journeys(
        self, origin: ProviderPlace, destination: ProviderPlace, journey_date: date
    ) -> tuple[DirectJourney, ...]:
        """Record a complete lookup and return the configured response or failure."""
        self.calls.append((origin, destination, journey_date))
        if self.error is not None:
            raise self.error
        return self.journeys


@pytest.fixture
def direct_provider(monkeypatch: pytest.MonkeyPatch) -> StubDirectJourneyProvider:
    """Replace capability wiring with a structural provider for deterministic search tests."""
    provider = StubDirectJourneyProvider()

    def select_provider() -> DirectJourneyProvider:
        """Return the configured provider without invoking concrete CTAN wiring."""
        return provider

    monkeypatch.setattr(service, "get_direct_journey_provider", select_provider)
    return provider


@pytest.fixture
def selected_places() -> tuple[CanonicalPlace, CanonicalPlace]:
    """Persist two canonical places with the active provider's independent external references."""
    origin = CanonicalPlace.objects.create(name="C\u00e1diz", municipality="C\u00e1diz")
    destination = CanonicalPlace.objects.create(name="Jerez", municipality="Jerez de la Frontera")
    ProviderPlaceReference.objects.create(provider_key="stub-direct", external_id="1", place=origin)
    ProviderPlaceReference.objects.create(
        provider_key="stub-direct", external_id="23", place=destination
    )
    return origin, destination


@pytest.fixture(autouse=True)
def isolated_direct_journey_cache() -> Iterator[None]:
    """Clear the direct-timetable cache around each scenario without flushing other tests."""
    key = service._cache_key("stub-direct", "1", "23", timezone.localdate())
    cache.delete(key)
    yield
    cache.delete(key)


pytestmark = pytest.mark.django_db


def test_service_filters_a_cached_complete_timetable(
    direct_provider: StubDirectJourneyProvider,
    selected_places: tuple[CanonicalPlace, CanonicalPlace],
) -> None:
    """Filter after cache retrieval so distinct time choices reuse one complete upstream result."""
    origin, destination = selected_places
    first = service.search_direct_journeys(
        origin.id, destination.id, timezone.localdate(), time(9, 30)
    )
    second = service.search_direct_journeys(origin.id, destination.id, timezone.localdate(), None)

    assert [journey.line_code for journey in first.catalog.journeys] == ["M-2"]
    assert [journey.line_code for journey in second.catalog.journeys] == ["M-1", "M-2"]
    assert len(direct_provider.calls) == 1
    assert direct_provider.calls[0][0].external_id == "1"
    assert direct_provider.calls[0][1].external_id == "23"


def test_api_returns_normalized_services_and_the_calendar_warning(
    client: Client,
    direct_provider: StubDirectJourneyProvider,
    selected_places: tuple[CanonicalPlace, CanonicalPlace],
) -> None:
    """Expose provider-independent journey cards and apply the optional departure-time threshold."""
    origin, destination = selected_places
    response = client.get(
        "/api/v1/journeys/direct",
        {
            "origin": str(origin.id),
            "destination": str(destination.id),
            "date": timezone.localdate().isoformat(),
            "depart_after": "09:30",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "origin": {
            "id": str(origin.id),
            "kind": "population_centre",
            "name": "C\u00e1diz",
            "municipality": "C\u00e1diz",
        },
        "destination": {
            "id": str(destination.id),
            "kind": "population_centre",
            "name": "Jerez",
            "municipality": "Jerez de la Frontera",
        },
        "date": timezone.localdate().isoformat(),
        "depart_after": "09:30:00",
        "fetched_at": response.json()["fetched_at"],
        "warnings": ["calendar_accuracy_not_guaranteed"],
        "items": [
            {
                "line_code": "M-2",
                "departure_time": "10:00:00",
                "arrival_time": "10:20:00",
                "duration_minutes": 20,
                "note": "Limited service",
            }
        ],
    }


@pytest.mark.parametrize(
    ("parameters", "code"),
    [
        ({"origin": "same", "destination": "same"}, "same_place"),
        (
            {"origin": "known", "destination": "known", "date": "2000-01-01"},
            "journey_date_unavailable",
        ),
    ],
)
def test_api_rejects_invalid_searches_before_provider_retrieval(
    client: Client,
    direct_provider: StubDirectJourneyProvider,
    selected_places: tuple[CanonicalPlace, CanonicalPlace],
    parameters: dict[str, str],
    code: str,
) -> None:
    """Return a typed response for matching places or dates outside CTAN's safe window."""
    origin, destination = selected_places
    request_parameters = {
        "origin": str(origin.id) if parameters["origin"] == "same" else str(origin.id),
        "destination": str(origin.id)
        if parameters["destination"] == "same"
        else str(destination.id),
        "date": parameters.get("date", timezone.localdate().isoformat()),
    }
    response = client.get("/api/v1/journeys/direct", request_parameters)

    assert response.status_code == 422
    assert response.json()["code"] == code
    assert direct_provider.calls == []


def test_api_distinguishes_unknown_places_and_provider_unavailability(
    client: Client,
    direct_provider: StubDirectJourneyProvider,
    selected_places: tuple[CanonicalPlace, CanonicalPlace],
) -> None:
    """Keep unknown IDs separate from a retryable provider failure without leaking its details."""
    origin, destination = selected_places
    unknown = client.get(
        "/api/v1/journeys/direct",
        {
            "origin": str(uuid4()),
            "destination": str(destination.id),
            "date": timezone.localdate().isoformat(),
        },
    )
    assert unknown.status_code == 404
    assert unknown.json()["code"] == "journey_place_not_found"

    direct_provider.error = ProviderError("Private CTAN details")
    unavailable = client.get(
        "/api/v1/journeys/direct",
        {
            "origin": str(origin.id),
            "destination": str(destination.id),
            "date": timezone.localdate().isoformat(),
        },
    )
    assert unavailable.status_code == 503
    assert unavailable.json()["code"] == "journeys_unavailable"


def test_api_documents_the_direct_journey_contract(client: Client) -> None:
    """Publish the typed direct journey endpoint and its public date parameter through OpenAPI."""
    schema = client.get("/api/v1/openapi.json").json()
    operation = schema["paths"]["/api/v1/journeys/direct"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/DirectJourneysResponse"
    }
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "origin",
        "destination",
        "date",
        "depart_after",
    }
