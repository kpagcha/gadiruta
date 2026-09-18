"""Verify CTAN direct-journey discovery, dated timetable parsing, and safe extraction."""

from datetime import time
from pathlib import Path

import httpx

from transport.domain import ProviderPlace, TransportMode
from transport.integrations.ctan.adapters import normalize_transport_mode, to_direct_journeys
from transport.integrations.ctan.client import CTANClient
from transport.integrations.ctan.schemas import CandidateLine, TimetablePlanner


def test_candidate_line_discovery_uses_the_verified_ctan_request(
    ctan_fixture_dir: Path,
) -> None:
    """Request CTAN's candidate endpoint with both references and deduplicate line IDs."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Record the request and return the captured C\u00e1diz-to-Jerez candidate response."""
        requests.append(request)
        return httpx.Response(
            200,
            content=(ctan_fixture_dir / "journeys_cadiz_jerez.json").read_bytes(),
        )

    with CTANClient(transport=httpx.MockTransport(respond)) as client:
        candidates = client.list_direct_candidate_lines("1", "23")

    assert [(candidate.upstream_id, candidate.code) for candidate in candidates] == [
        ("214", "MD"),
        ("158", "C-1"),
        ("177", "M-053"),
        ("36", "M-902"),
        ("18", "M-052"),
        ("38", "M-904"),
        ("16", "M-050"),
        ("17", "M-051"),
    ]
    assert requests[0].url.path.endswith("/horarios_origen_destino")
    assert dict(requests[0].url.params) == {"origen": "1", "destino": "23", "lang": "ES"}


def test_ctan_no_data_response_is_a_valid_empty_candidate_list(ctan_fixture_dir: Path) -> None:
    """Map CTAN's exact documented no-data response to a successful empty direct search."""
    with CTANClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                400,
                content=(ctan_fixture_dir / "journeys_no_data.json").read_bytes(),
            )
        )
    ) as client:
        assert client.list_direct_candidate_lines("23", "49") == []


def test_line_metadata_uses_the_verified_catalogue_request(ctan_fixture_dir: Path) -> None:
    """Fetch CTAN's line-ID-to-mode catalogue with an explicit Spanish language parameter."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Record the line catalogue request and return a representative saved response."""
        requests.append(request)
        return httpx.Response(200, content=(ctan_fixture_dir / "line_modes.json").read_bytes())

    with CTANClient(transport=httpx.MockTransport(respond)) as client:
        metadata = client.list_line_metadata()

    assert [(line.upstream_id, line.mode) for line in metadata] == [
        ("15", "BARCO"),
        ("158", "CERCANÍAS"),
        ("214", "MEDIA DISTANCIA"),
        ("16", "AUTOBUS"),
    ]
    assert requests[0].url.path.endswith("/lineas")
    assert dict(requests[0].url.params) == {"lang": "ES"}


def test_line_timetable_uses_only_ctans_day_and_month_parameters(
    ctan_fixture_dir: Path,
) -> None:
    """Fetch planners using CTAN's limited date contract without inventing a year parameter."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Record the dated line request and return a captured weekday timetable."""
        requests.append(request)
        return httpx.Response(200, content=(ctan_fixture_dir / "line_13_weekday.json").read_bytes())

    with CTANClient(transport=httpx.MockTransport(respond)) as client:
        planners = client.get_line_timetable("13", 15, 9)

    assert planners
    assert requests[0].url.path.endswith("/horarios_lineas")
    assert dict(requests[0].url.params) == {
        "linea": "13",
        "frecuencia": "",
        "dia": "15",
        "mes": "9",
        "lang": "ES",
    }


def test_timetable_extraction_uses_safe_group_matches_and_handles_midnight() -> None:
    """Use ordered groups, skip incomplete rows, and preserve an overnight service."""
    candidate = CandidateLine.model_validate({"idlinea": "9", "codigo": "N-9"})
    planner = TimetablePlanner.model_validate(
        {
            "nucleosIda": [
                {"colspan": 2, "nombre": "C\u00e1diz"},
                {"colspan": 1, "nombre": "Jerez"},
            ],
            "nucleosVuelta": [],
            "horarioIda": [
                {"horas": ["23:50", "--", "00:15"], "observaciones": " Night\u0000\nservice "},
                {"horas": ["--", "--", "00:30"]},
            ],
            "horarioVuelta": [],
        }
    )

    journeys = to_direct_journeys(
        ProviderPlace(external_id="1", name="Cadiz", municipality=None),
        ProviderPlace(external_id="23", name="Jerez", municipality=None),
        [candidate],
        {"9": [planner]},
        {"9": "BARCO"},
    )

    assert len(journeys) == 1
    assert journeys[0].line_code == "N-9"
    assert journeys[0].departure_time == time(23, 50)
    assert journeys[0].arrival_time == time(0, 15)
    assert journeys[0].duration_minutes == 25
    assert journeys[0].note == "Night service"
    assert journeys[0].transport_mode is TransportMode.BOAT


def test_transport_mode_normalization_has_a_safe_unknown_value() -> None:
    """Classify documented CTAN labels while keeping unforeseen labels safe for display."""
    assert normalize_transport_mode("CERCANÍAS") is TransportMode.TRAIN
    assert normalize_transport_mode("Trambahía") is TransportMode.TRAM
    assert normalize_transport_mode("unverified future mode") is TransportMode.UNKNOWN
