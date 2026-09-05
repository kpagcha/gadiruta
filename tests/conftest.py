"""Share offline HTTP safeguards and captured CTAN fixture locations across tests."""

from pathlib import Path
from typing import Never

import httpx
import pytest


@pytest.fixture(autouse=True)
def block_live_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject real HTTPX requests while allowing explicitly supplied mock transports."""

    def reject_network(*args: object, **kwargs: object) -> Never:
        """Fail immediately if a test attempts to use a real HTTP transport."""
        raise AssertionError("Tests must use httpx.MockTransport instead of live HTTP requests.")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", reject_network)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", reject_network)


@pytest.fixture
def ctan_fixture_dir() -> Path:
    """Locate saved provider responses independently of the runner's working directory."""
    return Path(__file__).parent / "fixtures" / "ctan"
