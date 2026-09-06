"""Gadiruta's versioned public API and generated contract."""

from typing import Literal

from django.http import HttpRequest
from ninja import NinjaAPI, Schema
from scalar_ninja import AgentConfig, ScalarConfig, ScalarViewer

from transport.api import router as places_router

api = NinjaAPI(
    title="Gadiruta API",
    description=(
        "Public transport information for the Cádiz area.\n\n"
        "Transport information is provided by the "
        "[Portal de Datos Abiertos de la Red de Consorcios de Transporte de Andalucía]"
        "(https://api.ctan.es/doc/).\n\n"
        "Gadiruta is an independent application, not an official CTAN or Junta de Andalucía "
        "service. No endorsement or affiliation is implied."
    ),
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
