"""Verify the provider boundary with saved responses and synthetic failure cases."""

import json
from pathlib import Path

import httpx
import pytest

from transport.integrations.ctan.adapters import to_places
from transport.integrations.ctan.client import CTANClient, CTANInvalidResponse, CTANUnavailable
from transport.integrations.ctan.schemas import PopulationCentre


def read_centres(payload: object) -> list[PopulationCentre]:
    """Pass a synthetic success payload through the real client parser without live HTTP."""
    with CTANClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as client:
        return client.list_population_centres()


def test_saved_catalogue_preserves_names_and_provider_relationships(ctan_fixture_dir: Path) -> None:
    """Normalize captured centres and municipalities without losing names or provider references."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Record request details and serve the corresponding captured catalogue response."""
        requests.append(request)
        filename = "municipios.json" if request.url.path.endswith("municipios/") else "nucleos.json"
        return httpx.Response(200, content=(ctan_fixture_dir / filename).read_bytes())

    with CTANClient(transport=httpx.MockTransport(respond)) as client:
        centres = client.list_population_centres()
        municipalities = client.list_municipalities()
    places = to_places(centres, municipalities)
    assert len(places) == 37
    assert len(municipalities) == 12
    assert all(place.municipality for place in places)
    airport = next(place for place in places if place.name == "Aeropuerto")
    assert airport.municipality == "Jerez de la Frontera"
    assert airport.provider == "ctan"
    assert airport.consortium_id == 2
    assert airport.upstream_id == "42"
    assert airport.upstream_municipality_id == "6"
    assert airport.upstream_zone == "K"
    assert [str(request.url) for request in requests] == [
        "https://api.ctan.es/v1/Consorcios/2/nucleos",
        "https://api.ctan.es/v1/Consorcios/2/municipios/",
    ]
    assert all(request.headers["accept"] == "application/json" for request in requests)
    assert all(request.extensions["timeout"]["connect"] == 3.0 for request in requests)
    assert all(request.extensions["timeout"]["read"] == 10.0 for request in requests)


def test_empty_list_is_a_valid_response(ctan_fixture_dir: Path) -> None:
    """Accept the captured empty-list shape as valid data rather than a provider failure."""
    payload = json.loads((ctan_fixture_dir / "nucleos_empty.json").read_text(encoding="utf-8"))
    assert read_centres(payload) == []


def test_inconsistent_records_are_skipped_and_identifiers_are_deduplicated(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Retain usable records, canonicalize IDs, and log invalid or duplicate entries."""
    records = read_centres(
        {
            "nucleos": [
                None,
                {"idNucleo": "bad", "nombre": "Invalid"},
                {"idNucleo": 1, "nombre": " Cádiz ", "extraField": "ignored"},
                {"idNucleo": "01", "nombre": "Duplicate"},
                {"idNucleo": "2", "nombre": "San Fernando"},
            ]
        }
    )
    assert [(record.upstream_id, record.name) for record in records] == [
        ("1", "Cádiz"),
        ("2", "San Fernando"),
    ]
    assert "invalid CTAN record" in caplog.text
    assert "duplicate CTAN identifier" in caplog.text


@pytest.mark.parametrize("identifier", [None, True, False, 0, -1, 1.5, "", "abc", "1/2", []])
def test_unusable_required_identifier_does_not_become_a_place(identifier: object) -> None:
    """Treat a nonempty catalogue with only an invalid ID as unusable, not empty."""
    with pytest.raises(CTANInvalidResponse, match="no usable records"):
        read_centres({"nucleos": [{"idNucleo": identifier, "nombre": "Invalid"}]})


@pytest.mark.parametrize("name", [None, "", "   ", 123, "a" * 256])
def test_unusable_required_name_does_not_become_a_place(name: object) -> None:
    """Reject records whose only display name is absent, blank, non-text, or too long."""
    with pytest.raises(CTANInvalidResponse, match="no usable records"):
        read_centres({"nucleos": [{"idNucleo": "1", "nombre": name}]})


@pytest.mark.parametrize(
    "optional_fields",
    [{}, {"idMunicipio": None, "idZona": None}, {"idMunicipio": "bad", "idZona": []}],
)
def test_missing_or_invalid_optional_fields_preserve_the_place(
    optional_fields: dict[str, object],
) -> None:
    """Preserve valid centre identity and name when optional references cannot be normalized."""
    centres = read_centres({"nucleos": [{"idNucleo": "1", "nombre": "Cádiz", **optional_fields}]})
    place = to_places(centres, [])[0]
    assert place.name == "Cádiz"
    assert place.municipality is None
    assert place.upstream_municipality_id is None
    assert place.upstream_zone is None


@pytest.mark.parametrize(
    "payload",
    [None, [], {}, {"nucleos": None}, {"nucleos": {}}, {"error": "failure", "nucleos": []}],
)
def test_invalid_envelope_is_not_treated_as_an_empty_catalogue(payload: object) -> None:
    """Reject invalid top-level shapes and error envelopes instead of inventing empty results."""
    with pytest.raises(CTANInvalidResponse):
        read_centres(payload)


def test_html_body_is_rejected_even_with_success_status(ctan_fixture_dir: Path) -> None:
    """Treat a successful HTTP status carrying HTML as an invalid provider response."""
    content = (ctan_fixture_dir / "consorcio_not_found.html").read_bytes()
    with (
        CTANClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content))
        ) as client,
        pytest.raises(CTANInvalidResponse, match="invalid JSON"),
    ):
        client.list_population_centres()


@pytest.mark.parametrize("status", [301, 400, 404, 429, 500, 503])
def test_http_failures_are_normalized(status: int, ctan_fixture_dir: Path) -> None:
    """Expose redirects and HTTP errors through the client's stable unavailability exception."""
    content = (ctan_fixture_dir / "nucleo_invalid_id.json").read_bytes()
    with (
        CTANClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(status, content=content))
        ) as client,
        pytest.raises(CTANUnavailable),
    ):
        client.list_population_centres()


@pytest.mark.parametrize(
    "error_type",
    [httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError],
)
def test_transport_failures_are_normalized(error_type: type[httpx.RequestError]) -> None:
    """Normalize connection, timeout, and protocol failures to CTANUnavailable."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Raise the selected transport failure with the originating request attached."""
        raise error_type("Upstream failure", request=request)

    with (
        CTANClient(transport=httpx.MockTransport(respond)) as client,
        pytest.raises(CTANUnavailable),
    ):
        client.list_population_centres()
