"""Gadiruta's versioned public API and generated contract."""

from typing import Literal

from django.http import HttpRequest
from ninja import NinjaAPI, Schema

api = NinjaAPI(title="Gadiruta API", version="1.0.0", urls_namespace="api-v1")


class HealthResponse(Schema):
    status: Literal["ok"]


@api.get("/health", response=HealthResponse, tags=["System"], auth=None)
def health(request: HttpRequest) -> HealthResponse:
    """Check application liveness; does not check PostgreSQL or CTAN availability."""
    return HealthResponse(status="ok")
