"""Verify CTAN's place capability translates retrieval failures and releases HTTP resources."""

from pathlib import Path

import httpx
import pytest

from transport.integrations.ctan.client import CTANError, CTANInvalidResponse, CTANUnavailable
from transport.integrations.ctan.provider import CTANPlaceProvider
from transport.providers.base import PlaceProvider, ProviderError
from transport.providers.wiring import get_place_provider


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


def test_provider_returns_the_saved_catalogue_and_closes_http(ctan_fixture_dir: Path) -> None:
    """Expose joined public places through the capability contract and close the owned transport."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Serve the verified resource requested by the real integration client."""
        filename = "municipios.json" if request.url.path.endswith("municipios/") else "nucleos.json"
        return httpx.Response(200, content=(ctan_fixture_dir / filename).read_bytes())

    transport = TrackedTransport(respond)
    provider: PlaceProvider = CTANPlaceProvider(transport=transport)
    places = provider.get_places()
    assert len(places) == 37
    assert all(place.municipality for place in places)
    assert str(next(place.id for place in places if place.name == "Cádiz")) == (
        "a222989e-0a14-5920-872e-5ae77baea6b7"
    )
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
