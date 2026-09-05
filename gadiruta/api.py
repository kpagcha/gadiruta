"""Gadiruta's versioned public API and generated contract."""

from typing import Literal

from django.http import HttpRequest
from ninja import NinjaAPI, Schema

from transport.api import router as places_router

api = NinjaAPI(title="Gadiruta API", version="1.0.0", urls_namespace="api-v1")
api.add_router("", places_router)


class HealthResponse(Schema):
    """Confirm that the API responded to a health request."""

    status: Literal["ok"]


@api.get("/health", response=HealthResponse, tags=["System"], auth=None)
def health(request: HttpRequest) -> HealthResponse:
    """Check whether the API is responding."""
    return HealthResponse(status="ok")
