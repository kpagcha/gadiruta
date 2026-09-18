"""Verify CTAN capabilities translate retrieval failures and release HTTP resources."""

from datetime import date
from pathlib import Path

import httpx
import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

from transport.domain import ProviderPlace
from transport.integrations.ctan.client import CTANError, CTANInvalidResponse, CTANUnavailable
from transport.integrations.ctan.provider import (
    LINE_MODE_CACHE_KEY,
    CTANDirectJourneyProvider,
    CTANPlaceProvider,
)
from transport.providers.base import DirectJourneyProvider, PlaceProvider, ProviderError
from transport.providers.wiring import get_direct_journey_provider, get_place_provider


class TrackedTransport(httpx.MockTransport):
    """Serve in-memory HTTP responses while recording cleanup by the owning client."""

    is_closed = False

    def close(self) -> None:
        """Record that the provider released its HTTP transport after the fetch."""
        self.is_closed = True
        super().close()


def test_default_place_provider_is_ctan() -> None:
    """Keep the current Cádiz provider selected at the single application wiring point."""
    assert isinstance(get_place_provider(), CTANPlaceProvider)


def test_default_direct_journey_provider_is_ctan() -> None:
    """Keep CTAN selected behind the separate direct-journey capability boundary."""
    assert isinstance(get_direct_journey_provider(), CTANDirectJourneyProvider)


def test_unsupported_configured_place_provider_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a configured provider before an unsupported implementation can serve data."""
    monkeypatch.setattr(settings, "GADIRUTA_PLACE_PROVIDER", "unsupported")
    with pytest.raises(ImproperlyConfigured, match="GADIRUTA_PLACE_PROVIDER"):
        get_place_provider()


def test_unsupported_configured_direct_journey_provider_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a direct-search implementation before an unsupported provider can serve results."""
    monkeypatch.setattr(settings, "GADIRUTA_DIRECT_JOURNEY_PROVIDER", "unsupported")
    with pytest.raises(ImproperlyConfigured, match="GADIRUTA_DIRECT_JOURNEY_PROVIDER"):
        get_direct_journey_provider()


def test_direct_journey_provider_composes_candidate_and_dated_timetable_requests() -> None:
    """Produce services with a cached line mode and a dated timetable fetch."""
    cache.delete(LINE_MODE_CACHE_KEY)
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Serve a small CTAN-shaped discovery or line table based on the requested path."""
        requests.append(request)
        if request.url.path.endswith("horarios_origen_destino"):
            return httpx.Response(200, json={"horario": [{"idlinea": "9", "codigo": "N-9"}]})
        if request.url.path.endswith("/lineas"):
            return httpx.Response(200, json={"lineas": [{"idLinea": "9", "modo": "BARCO"}]})
        return httpx.Response(
            200,
            json={
                "planificadores": [
                    {
                        "nucleosIda": [
                            {"colspan": 1, "nombre": "C\u00e1diz"},
                            {"colspan": 1, "nombre": "Jerez"},
                        ],
                        "nucleosVuelta": [],
                        "horarioIda": [{"horas": ["09:00", "09:35"]}],
                        "horarioVuelta": [],
                    }
                ]
            },
        )

    provider: DirectJourneyProvider = CTANDirectJourneyProvider(
        transport=httpx.MockTransport(respond)
    )
    journeys = provider.get_direct_journeys(
        origin=ProviderPlace(external_id="1", name="C\u00e1diz", municipality=None),
        destination=ProviderPlace(external_id="14", name="Jerez", municipality=None),
        journey_date=date(2026, 9, 14),
    )

    assert [(journey.line_code, journey.duration_minutes) for journey in journeys] == [("N-9", 35)]
    assert journeys[0].transport_mode.value == "boat"
    provider.get_direct_journeys(
        origin=ProviderPlace(external_id="1", name="Cádiz", municipality=None),
        destination=ProviderPlace(external_id="14", name="Jerez", municipality=None),
        journey_date=date(2026, 9, 15),
    )
    assert sum(request.url.path.endswith("/lineas") for request in requests) == 1
    cache.delete(LINE_MODE_CACHE_KEY)


def test_direct_journey_provider_rejects_partial_timetables() -> None:
    """Translate one candidate line failure into a neutral complete-result provider error."""
    cache.delete(LINE_MODE_CACHE_KEY)

    def respond(request: httpx.Request) -> httpx.Response:
        """Return a candidate line then make its dated timetable unavailable."""
        if request.url.path.endswith("horarios_origen_destino"):
            return httpx.Response(200, json={"horario": [{"idlinea": "9", "codigo": "N-9"}]})
        return httpx.Response(503)

    provider = CTANDirectJourneyProvider(transport=httpx.MockTransport(respond))
    with pytest.raises(ProviderError, match="complete timetable"):
        provider.get_direct_journeys(
            origin=ProviderPlace(external_id="1", name="C\u00e1diz", municipality=None),
            destination=ProviderPlace(external_id="14", name="Jerez", municipality=None),
            journey_date=date(2026, 9, 14),
        )
    cache.delete(LINE_MODE_CACHE_KEY)


def test_provider_returns_the_saved_catalogue_and_closes_http(ctan_fixture_dir: Path) -> None:
    """Expose joined provider places through the capability contract and close the transport."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Serve the verified resource requested by the real integration client."""
        filename = "municipios.json" if request.url.path.endswith("municipios/") else "nucleos.json"
        return httpx.Response(200, content=(ctan_fixture_dir / filename).read_bytes())

    transport = TrackedTransport(respond)
    provider: PlaceProvider = CTANPlaceProvider(transport=transport)
    places = provider.get_places()
    assert len(places) == 37
    assert all(place.municipality for place in places)
    assert next(place.external_id for place in places if place.name == "Cádiz") == "1"
    assert transport.is_closed


@pytest.mark.parametrize("resource", ["nucleos", "municipios/"])
@pytest.mark.parametrize(
    ("failure", "cause_type"),
    [
        (httpx.Response(503), CTANUnavailable),
        (httpx.ReadTimeout("Private timeout details"), CTANUnavailable),
        (httpx.Response(200, text="<html>Private error</html>"), CTANInvalidResponse),
        (httpx.Response(200, json={"unexpected": []}), CTANInvalidResponse),
    ],
)
def test_provider_translates_client_errors_and_closes_http(
    resource: str, failure: httpx.Response | httpx.HTTPError, cause_type: type[CTANError]
) -> None:
    """Map either resource's transport and validation errors to the neutral provider exception."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Fail the selected resource after supplying a valid centre if required."""
        if request.url.path.endswith(resource):
            if isinstance(failure, httpx.HTTPError):
                raise failure
            return failure
        return httpx.Response(200, json={"nucleos": [{"idNucleo": "1", "nombre": "Cádiz"}]})

    transport = TrackedTransport(respond)
    with pytest.raises(ProviderError) as error:
        CTANPlaceProvider(transport=transport).get_places()
    assert not isinstance(error.value, CTANError)
    assert isinstance(error.value.__cause__, cause_type)
    assert str(error.value) == "The place provider could not supply a usable catalogue."
    assert transport.is_closed
