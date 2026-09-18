"""Implement the place capability with CTAN's verified Cádiz catalogue resources."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date

import httpx

from transport.domain import DirectJourney, ProviderPlace
from transport.integrations.ctan.adapters import to_direct_journeys, to_places
from transport.integrations.ctan.client import CONSORTIUM_ID, CTANClient, CTANError
from transport.integrations.ctan.schemas import TimetablePlanner
from transport.providers.base import ProviderError

CTAN_PLACE_PROVIDER_KEY = f"ctan:consortium:{CONSORTIUM_ID}:population-centre"


class CTANPlaceProvider:
    """Join CTAN centres and municipality labels behind the normalized place contract."""

    provider_key = CTAN_PLACE_PROVIDER_KEY

    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        """Allow an offline HTTP transport; each catalogue fetch owns and closes its client."""
        self._transport = transport

    def get_places(self) -> tuple[ProviderPlace, ...]:
        """Fetch normalized places and translate CTAN failures to ProviderError.

        Empty centre lists skip the municipality request. Unusable data from either resource
        fails the whole fetch, while the client continues to tolerate individual bad records.
        """
        try:
            with CTANClient(transport=self._transport) as client:
                centres = client.list_population_centres()
                municipalities = client.list_municipalities() if centres else []
            return to_places(centres, municipalities)
        except CTANError as error:
            raise ProviderError(
                "The place provider could not supply a usable catalogue."
            ) from error


class CTANDirectJourneyProvider:
    """Compose CTAN candidate lines and dated timetables into complete direct journey services."""

    provider_key = CTAN_PLACE_PROVIDER_KEY

    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        """Allow offline transports while each discovery or line fetch owns its HTTP client."""
        self._transport = transport

    def get_direct_journeys(
        self, origin: ProviderPlace, destination: ProviderPlace, journey_date: date
    ) -> tuple[DirectJourney, ...]:
        """Return all safely extractable CTAN rows or translate any provider failure.

        Candidate line IDs are deduplicated by the client. Four bounded concurrent line requests
        avoid serial latency while preserving the complete-result policy on any failure.
        """
        try:
            with CTANClient(transport=self._transport) as client:
                candidates = client.list_direct_candidate_lines(
                    origin.external_id, destination.external_id
                )
            if not candidates:
                return ()
            with ThreadPoolExecutor(max_workers=min(4, len(candidates))) as executor:
                futures = {
                    candidate.upstream_id: executor.submit(
                        self._get_line_timetable, candidate.upstream_id, journey_date
                    )
                    for candidate in candidates
                }
                planners_by_line = {
                    candidate.upstream_id: futures[candidate.upstream_id].result()
                    for candidate in candidates
                }
            return to_direct_journeys(origin, destination, candidates, planners_by_line)
        except CTANError as error:
            raise ProviderError(
                "The direct journey provider could not supply a complete timetable."
            ) from error

    def _get_line_timetable(self, line_id: str, journey_date: date) -> list[TimetablePlanner]:
        """Fetch one candidate line in an isolated client suitable for bounded parallel work."""
        with CTANClient(transport=self._transport) as client:
            return client.get_line_timetable(line_id, journey_date.day, journey_date.month)
