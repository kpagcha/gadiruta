"""Small synchronous CTAN client with bounded requests and validated records."""

import logging
from types import TracebackType
from typing import Self

import httpx
from pydantic import ValidationError

from transport.integrations.ctan.schemas import CTANRecord, Municipality, PopulationCentre

logger = logging.getLogger(__name__)
CONSORTIUM_ID = 2
BASE_URL = f"https://api.ctan.es/v1/Consorcios/{CONSORTIUM_ID}/"


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

    def _get_records[T: CTANRecord](self, path: str, key: str, schema: type[T]) -> list[T]:
        """Fetch and validate a named record list, retaining the first valid record per ID.

        Raise CTANUnavailable for HTTP or transport failures and CTANInvalidResponse for
        unusable JSON, envelopes, or nonempty lists with no valid records. Empty lists are valid.
        """
        try:
            response = self._http.get(path)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise CTANUnavailable("CTAN request failed.") from error

        try:
            payload = response.json()
        except ValueError as error:
            raise CTANInvalidResponse("CTAN returned invalid JSON.") from error
        if not isinstance(payload, dict) or "error" in payload:
            raise CTANInvalidResponse("CTAN returned an unexpected response.")
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
            if item.upstream_id in seen:
                logger.warning("Skipping a duplicate CTAN identifier in %s.", key)
                continue
            seen.add(item.upstream_id)
            parsed.append(item)
        if records and not parsed:
            raise CTANInvalidResponse(f"CTAN returned no usable records in {key}.")
        return parsed
