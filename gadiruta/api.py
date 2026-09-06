"""Gadiruta's versioned public API and generated contract."""

from typing import Literal

from django.http import HttpRequest
from ninja import NinjaAPI, Schema
from scalar_ninja import AgentConfig, ScalarConfig, ScalarViewer

from transport.api import router as places_router

api = NinjaAPI(
    title="Gadiruta API",
    version="1.0.0",
    urls_namespace="api-v1",
    docs=ScalarViewer(
        ScalarConfig(
            title="Gadiruta API reference",
            openapi_url="/api/v1/openapi.json",
            scalar_js_url=(
                "https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.67.0"
                "/dist/browser/standalone.js"
            ),
            scalar_favicon_url="data:,",
            agent=AgentConfig(disabled=True),
        )
    ),
)
api.add_router("", places_router)


class HealthResponse(Schema):
    """Confirm that the API responded to a health request."""

    status: Literal["ok"]


@api.get("/health", response=HealthResponse, tags=["System"], auth=None)
def health(request: HttpRequest) -> HealthResponse:
    """Check whether the API is responding."""
    return HealthResponse(status="ok")
