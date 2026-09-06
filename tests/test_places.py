"""Exercise cached place search through Django with an offline CTAN transport."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from django.core.cache import cache
from django.test import Client

from transport.integrations.ctan.provider import CTANPlaceProvider
from transport.services import places as service

NUCLEOS = "/v1/Consorcios/2/nucleos"
MUNICIPIOS = "/v1/Consorcios/2/municipios/"


@dataclass
class CTANMock:
    """Serve replaceable provider responses or errors while recording outgoing requests."""

    responses: dict[str, httpx.Response | httpx.HTTPError]
    requests: list[httpx.Request] = field(default_factory=list)

    def respond(self, request: httpx.Request) -> httpx.Response:
        """Record the request and return or raise the outcome configured for its URL path."""
        self.requests.append(request)
        response = self.responses[request.url.path]
        if isinstance(response, httpx.HTTPError):
            raise response
        return response


@pytest.fixture
def ctan(monkeypatch: pytest.MonkeyPatch, ctan_fixture_dir: Path) -> CTANMock:
    """Exercise the real CTAN provider through the API using saved offline HTTP responses."""
    upstream = CTANMock(
        responses={
            NUCLEOS: httpx.Response(200, content=(ctan_fixture_dir / "nucleos.json").read_bytes()),
            MUNICIPIOS: httpx.Response(
                200, content=(ctan_fixture_dir / "municipios.json").read_bytes()
            ),
        }
    )
    monkeypatch.setattr(
        service,
        "get_place_provider",
        lambda: CTANPlaceProvider(transport=httpx.MockTransport(upstream.respond)),
    )
    return upstream


@pytest.mark.parametrize("query", ["cadiz", "CÁDIZ", "  Cádiz  ", "Ca\u0301diz"])
def test_search_normalizes_accents_case_and_whitespace(
    client: Client, ctan: CTANMock, query: str
) -> None:
    """Return the same Cádiz place for case, accent, Unicode, and whitespace variants."""
    response = client.get("/api/v1/places", {"q": query})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    place = body["items"][0]
    assert UUID(place["id"]).version == 5
    assert place == {
        "id": "a222989e-0a14-5920-872e-5ae77baea6b7",
        "kind": "population_centre",
        "name": "Cádiz",
        "municipality": "Cádiz",
    }
    assert datetime.fromisoformat(body["fetched_at"]).utcoffset() == timedelta(0)
    assert len(ctan.requests) == 2


def test_exact_name_precedes_other_centres_in_the_same_municipality(
    client: Client, ctan: CTANMock
) -> None:
    """Rank Jerez itself ahead of municipality-only matches while respecting the result limit."""
    response = client.get("/api/v1/places", {"q": "jerez", "limit": 2})
    assert [place["name"] for place in response.json()["items"]] == ["Jerez", "Aeropuerto"]
    assert all(
        place["municipality"] == "Jerez de la Frontera" for place in response.json()["items"]
    )


def test_search_can_combine_municipality_and_centre_tokens(client: Client, ctan: CTANMock) -> None:
    """Match a query whose tokens are split between the centre and municipality labels."""
    response = client.get("/api/v1/places", {"q": "jerez aeropuerto"})
    assert [place["name"] for place in response.json()["items"]] == ["Aeropuerto"]


def test_prefix_name_precedes_substring_name_and_municipality_matches(
    client: Client, ctan: CTANMock
) -> None:
    """Prefer centre-name prefixes and sort equally ranked substring matches consistently."""
    response = client.get("/api/v1/places", {"q": "puerto", "limit": 50})
    assert [place["name"] for place in response.json()["items"][:3]] == [
        "Puerto Real",
        "Aeropuerto",
        "El Puerto de Santa María",
    ]


@pytest.mark.parametrize("query", ["", " ", "a", " á ", "\u0301"])
def test_short_queries_do_not_fetch_a_catalogue(client: Client, query: str) -> None:
    """Skip HTTP and return no timestamp when fewer than two normalized characters remain."""
    # A live request here would fail through the default network-blocking fixture.
    response = client.get("/api/v1/places", {"q": query})
    assert response.status_code == 200
    assert response.json() == {"items": [], "fetched_at": None}


def test_missing_query_does_not_fetch_a_catalogue(client: Client) -> None:
    """Treat an omitted query as empty input without contacting the provider."""
    assert client.get("/api/v1/places").json() == {"items": [], "fetched_at": None}


@pytest.mark.parametrize(
    "parameters",
    [{"q": "x" * 101}, {"q": "cadiz", "limit": 0}, {"limit": 51}, {"limit": "invalid"}],
)
def test_invalid_parameters_are_rejected_before_fetching(
    client: Client, parameters: dict[str, object]
) -> None:
    """Reject excessive query length and invalid limits before any provider request."""
    assert client.get("/api/v1/places", parameters).status_code == 422


def test_no_matching_places_is_a_successful_search(client: Client, ctan: CTANMock) -> None:
    """Return an empty result with the catalogue timestamp when valid data has no matches."""
    response = client.get("/api/v1/places", {"q": "not-a-place"})
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["fetched_at"] is not None


def test_unknown_municipality_keeps_the_place_searchable(client: Client, ctan: CTANMock) -> None:
    """Return a centre with an unknown municipality label when its reference cannot be resolved."""
    ctan.responses[NUCLEOS] = httpx.Response(
        200, json={"nucleos": [{"idNucleo": "1", "nombre": "Cádiz", "idMunicipio": "999999"}]}
    )
    response = client.get("/api/v1/places", {"q": "cadiz"})
    assert response.status_code == 200
    assert response.json()["items"][0]["municipality"] is None


def test_empty_catalogue_is_cached_without_a_municipality_request(
    client: Client, ctan: CTANMock, ctan_fixture_dir: Path
) -> None:
    """Cache a valid empty catalogue and avoid fetching municipality labels it cannot use."""
    ctan.responses[NUCLEOS] = httpx.Response(
        200, content=(ctan_fixture_dir / "nucleos_empty.json").read_bytes()
    )
    first = client.get("/api/v1/places", {"q": "cadiz"})
    second = client.get("/api/v1/places", {"q": "jerez"})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["items"] == []
    assert first.json()["fetched_at"] is not None
    assert len(ctan.requests) == 1


def test_catalogue_cache_is_shared_across_queries_and_limits(
    client: Client, ctan: CTANMock
) -> None:
    """Reuse an unexpired snapshot across searches even when the provider becomes unavailable."""
    first = client.get("/api/v1/places", {"q": "cadiz"}).json()
    ctan.responses[NUCLEOS] = httpx.Response(503)
    second = client.get("/api/v1/places", {"q": "jerez", "limit": 2})
    assert second.status_code == 200
    assert second.json()["fetched_at"] == first["fetched_at"]
    assert len(second.json()["items"]) == 2
    assert len(ctan.requests) == 2


def test_expired_catalogue_can_refresh_without_changing_place_ids(
    client: Client, ctan: CTANMock, ctan_fixture_dir: Path
) -> None:
    """Refresh names and record order after expiry without changing public place identity."""
    first = client.get("/api/v1/places", {"q": "cadiz"}).json()["items"][0]
    payload = json.loads((ctan_fixture_dir / "nucleos.json").read_text(encoding="utf-8"))
    payload["nucleos"].reverse()
    for record in payload["nucleos"]:
        if record["idNucleo"] == "1":
            record["nombre"] = "Cádiz centro"
    ctan.responses[NUCLEOS] = httpx.Response(200, json=payload)
    cache.touch(service.CACHE_KEY, timeout=0)
    second = client.get("/api/v1/places", {"q": "cadiz"}).json()["items"][0]
    assert second["id"] == first["id"]
    assert second["name"] == "Cádiz centro"
    assert len(ctan.requests) == 4


@pytest.mark.parametrize("resource", [NUCLEOS, MUNICIPIOS])
def test_upstream_errors_return_503_and_are_not_cached(
    client: Client, ctan: CTANMock, resource: str
) -> None:
    """Return a safe 503 for either catalogue request and recover on a later successful fetch."""
    valid_response = ctan.responses[resource]
    ctan.responses[resource] = httpx.Response(503, text="Private provider error details")
    failed = client.get("/api/v1/places", {"q": "cadiz"})
    assert failed.status_code == 503
    assert failed.json() == {
        "code": "places_unavailable",
        "message": "Place search is temporarily unavailable. Please try again later.",
    }
    ctan.responses[resource] = valid_response
    recovered = client.get("/api/v1/places", {"q": "cadiz"})
    assert recovered.status_code == 200
    assert recovered.json()["items"][0]["name"] == "Cádiz"


@pytest.mark.parametrize(
    "failure",
    [
        httpx.ReadTimeout("Private timeout details"),
        httpx.Response(200, text="<html>Provider error</html>"),
        httpx.Response(200, json={"nucleos": None}),
        httpx.Response(200, json={"nucleos": [{"nombre": "Missing identifier"}]}),
    ],
)
def test_unusable_provider_data_is_reported_as_unavailable(
    client: Client, ctan: CTANMock, failure: httpx.Response | httpx.HTTPError
) -> None:
    """Expose timeouts and unusable payloads as temporary unavailability, not empty results."""
    ctan.responses[NUCLEOS] = failure
    response = client.get("/api/v1/places", {"q": "cadiz"})
    assert response.status_code == 503
    assert response.json()["code"] == "places_unavailable"


def test_expired_cache_does_not_hide_refresh_failures(client: Client, ctan: CTANMock) -> None:
    """Report unavailability on a failed refresh without falling back to an expired snapshot."""
    assert client.get("/api/v1/places", {"q": "cadiz"}).status_code == 200
    cache.touch(service.CACHE_KEY, timeout=0)
    ctan.responses[NUCLEOS] = httpx.Response(503)
    assert client.get("/api/v1/places", {"q": "cadiz"}).status_code == 503


def test_openapi_describes_place_queries_and_unavailability(client: Client) -> None:
    """Publish query bounds and typed success and unavailability responses in OpenAPI."""
    schema = client.get("/api/v1/openapi.json").json()
    operation = schema["paths"]["/api/v1/places"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PlacesResponse"
    }
    assert operation["responses"]["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PlacesUnavailableResponse"
    }
    parameters = {parameter["name"]: parameter["schema"] for parameter in operation["parameters"]}
    assert parameters["q"]["maxLength"] == 100
    assert parameters["limit"]["minimum"] == 1
    assert parameters["limit"]["maximum"] == 50
