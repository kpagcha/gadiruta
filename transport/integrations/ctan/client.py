"""Small synchronous CTAN client with bounded requests and validated records."""

import logging
from types import TracebackType
from typing import Self, cast

import httpx
from pydantic import ValidationError

from transport.integrations.ctan.schemas import (
    CandidateLine,
    CTANRecord,
    Municipality,
    PopulationCentre,
    TimetablePlanner,
)

logger = logging.getLogger(__name__)
CONSORTIUM_ID = 2
BASE_URL = f"https://api.ctan.es/v1/Consorcios/{CONSORTIUM_ID}/"
NO_DATA_ERROR = "No se encuentran los datos"


class CTANError(Exception):
    """The provider could not supply usable data."""


class CTANUnavailable(CTANError):
    """An HTTP or transport failure prevented a successful request."""


class CTANInvalidResponse(CTANError):
    """The provider response did not contain the expected data."""


class CTANClient:
    """Own a synchronous HTTP session for validated Cádiz catalogue requests.

    Use as a context manager to release connections on success or failure. HTTP and payload
    failures are normalized to CTANError subclasses; individual unusable records are skipped.
    """

    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        """Configure HTTPS requests with timeouts and an optional transport for offline tests."""
        self._http = httpx.Client(
            base_url=BASE_URL,
            timeout=httpx.Timeout(10.0, connect=3.0),
            headers={"Accept": "application/json"},
            transport=transport,
        )

    def __enter__(self) -> Self:
        """Return this client for catalogue operations inside a managed block."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the owned HTTP session without suppressing exceptions from the managed block."""
        self._http.close()

    def list_population_centres(self) -> list[PopulationCentre]:
        """Fetch the consortium's centre list and return validated, unique records."""
        return self._get_records("nucleos", "nucleos", PopulationCentre)

    def list_municipalities(self) -> list[Municipality]:
        """Fetch municipality records used to resolve centre display labels."""
        return self._get_records("municipios/", "municipios", Municipality)

    def list_direct_candidate_lines(
        self, origin_id: str, destination_id: str
    ) -> list[CandidateLine]:
        """Discover distinct candidate lines, accepting CTAN's documented no-data response."""
        payload = self._get_json(
            "horarios_origen_destino",
            params={"origen": origin_id, "destino": destination_id, "lang": "ES"},
            allow_no_data=True,
        )
        if payload is None:
            return []
        return self._parse_records(payload, "horario", CandidateLine)

    def get_line_timetable(self, line_id: str, day: int, month: int) -> list[TimetablePlanner]:
        """Fetch dated line planners whose CTAN date has no reliable explicit year parameter."""
        payload = self._get_json(
            "horarios_lineas",
            params={
                "linea": line_id,
                "frecuencia": "",
                "dia": str(day),
                "mes": str(month),
                "lang": "ES",
            },
        )
        assert payload is not None
        return self._parse_records(payload, "planificadores", TimetablePlanner)

    def _get_records[T: CTANRecord](self, path: str, key: str, schema: type[T]) -> list[T]:
        """Fetch and validate a named record list, retaining the first valid record per ID.

        Raise CTANUnavailable for HTTP or transport failures and CTANInvalidResponse for
        unusable JSON, envelopes, or nonempty lists with no valid records. Empty lists are valid.
        """
        payload = self._get_json(path)
        assert payload is not None
        return self._parse_records(payload, key, schema)

    def _get_json(
        self, path: str, *, params: dict[str, str] | None = None, allow_no_data: bool = False
    ) -> dict[str, object] | None:
        """Fetch one JSON object, optionally mapping CTAN's exact no-data error to None."""
        try:
            response = self._http.get(path, params=params)
        except httpx.HTTPError as error:
            raise CTANUnavailable("CTAN request failed.") from error
        if not (allow_no_data and response.status_code == 400):
            try:
                response.raise_for_status()
            except httpx.HTTPError as error:
                raise CTANUnavailable("CTAN request failed.") from error
        try:
            payload = response.json()
        except ValueError as error:
            raise CTANInvalidResponse("CTAN returned invalid JSON.") from error
        if allow_no_data and response.status_code == 400 and payload == {"error": NO_DATA_ERROR}:
            return None
        try:
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise CTANUnavailable("CTAN request failed.") from error
        if not isinstance(payload, dict) or "error" in payload:
            raise CTANInvalidResponse("CTAN returned an unexpected response.")
        return payload

    def _parse_records[T: CTANRecord | TimetablePlanner](
        self, payload: dict[str, object], key: str, schema: type[T]
    ) -> list[T]:
        """Validate one CTAN record list while retaining independently usable records."""
        records = payload.get(key)
        if not isinstance(records, list):
            raise CTANInvalidResponse(f"CTAN response is missing the {key} list.")
        parsed: list[T] = []
        seen: set[str] = set()
        for record in records:
            try:
                item = schema.model_validate(record)
            except ValidationError:
                logger.warning("Skipping an invalid CTAN record in %s.", key)
                continue
            identifier = item.upstream_id if isinstance(item, CTANRecord) else None
            if identifier is not None and identifier in seen:
                logger.warning("Skipping a duplicate CTAN identifier in %s.", key)
                continue
            if identifier is not None:
                seen.add(identifier)
            parsed.append(cast(T, item))
        if records and not parsed:
            raise CTANInvalidResponse(f"CTAN returned no usable records in {key}.")
        return parsed
