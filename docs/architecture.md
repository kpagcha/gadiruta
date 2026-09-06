# Architecture

## Overview

Gadiruta uses a separated frontend/backend architecture within a single Git repository.

```text
Browser / React
       ↓
  Django API
       ↓
 Transport domain/services
       ↓
  CTAN adapter
       ↓
    CTAN API
```

The frontend must never depend directly on CTAN's API shape.

---

## Repository layout

Current structure (the Django scaffold remains at the repository root):

```text
gadiruta/
    AGENTS.md
    README.md
    manage.py
    pyproject.toml
    uv.lock
    gadiruta/        # Django settings, root API, and URL configuration
    transport/       # Public transport API, services, and CTAN integration
    frontend/        # React application and frontend tooling
    tests/
    docs/
```

Backend and frontend run independently but are versioned together. A move to `backend/` is
unnecessary for the first slices.

---

## Backend

Stack:

- Python.
- Django 6.1.1.
- Django Ninja.
- PostgreSQL.
- httpx.
- pytest / pytest-django.

The root `gadiruta/api.py` owns the versioned Ninja API and application liveness endpoint. Runtime
configuration comes from the environment and uses PostgreSQL; the default timezone is Europe/Madrid
with Django timezone support enabled. The root API mounts the transport place-search router.

Implemented transport organization at the repository root:

```text
transport/
    api.py
    schemas.py
    domain.py
    services/
        places.py
    integrations/
        ctan/
            client.py
            schemas.py
            adapters.py
```

Responsibilities:

### Django API layer

- Expose Gadiruta's stable API contract.
- Validate query/path/body parameters.
- Return normalized response schemas.
- Generate OpenAPI documentation.

### Domain/service layer

- Implement transport-related application behavior.
- Avoid direct coupling to HTTP or React concerns.
- Coordinate normalized provider data.

### CTAN integration layer

- Perform upstream HTTP requests.
- Parse and validate CTAN responses.
- Normalize provider-specific fields.
- Isolate CTAN-specific identifiers and quirks.

Raw CTAN payloads must not become Gadiruta's public API contract.

The HTTP client validates provider records with Pydantic. The adapter produces immutable domain
values with separate provider references and public Gadiruta IDs. Place search joins municipality
names, caches the normalized catalogue, and performs local accent-insensitive matching and ranking.
The API explicitly selects public fields; upstream identifiers and zone fields remain internal.
The transport package has no Django models or migrations yet.

---

## Frontend

Stack:

- React 19.
- TypeScript.
- Vite.
- React Router.
- TanStack Query.
- react-i18next.

Implemented organization:

```text
frontend/
    src/
        api/
        components/
        features/
            journey-search/
        pages/
        i18n/
            en.json
            es.json
        styles/
```

Responsibilities:

- User interaction.
- Search state.
- Routing.
- Query caching.
- Responsive presentation.
- Localization.
- localStorage-based language preference. Recent searches and favorites are not implemented yet.

React Router supplies the homepage and a localized not-found page. Each autocomplete keeps draft
text separate from a confirmed public place identity. TanStack Query shares suggestion results
between fields, debounces requests by 250 ms, and cancels obsolete requests. Suggestions have a
five-minute freshness window and a ten-minute inactive lifetime; failed requests are not automatically
retried, and the error state offers a retry control.
The API client validates response shape and imposes a 25-second request timeout.

Browser requests use relative `/api/v1/` URLs. Vite proxies `/api/` to Django on port 8000 during
development and local build preview, so no cross-origin API configuration is needed. Production
hosting is not configured: it will need same-origin API forwarding and SPA fallback for UI routes.

---

## API boundary

The frontend calls Gadiruta's Django API, mounted at `/api/v1/`. Application liveness deliberately
does not contact a database or upstream provider. Place search uses the CTAN adapter on cache
misses and does not require a database. The remaining resource plans are in `docs/features.md`.

Django Ninja/OpenAPI is the canonical endpoint-level reference.

---

## Persistence and caching

The initial population-centre catalogue uses Django's default local-memory cache with a one-hour
TTL, shared across search queries within each process. The timestamp reflects the completed fetch,
not the upstream publication time. A valid empty catalogue is cacheable; failures are not. Invalid
individual records are skipped, but a nonempty response containing no usable records is an error.
An unexpired catalogue can serve requests during provider outages. There is no stale-on-error
fallback after expiry, background refresh, or shared multi-worker cache yet. Concurrent cold
requests can perform duplicate fetches.

Public place IDs use deterministic UUIDs derived from scoped provider identity, independently of
display names and catalogue order; see `docs/decisions.md`. No transport data is persisted yet.

PostgreSQL may hold normalized or cached provider data.

Potential persisted entities include:

- Stops.
- Locations/population centres.
- Lines.
- Operators.
- Timetables.
- Route geometry.
- Synchronization metadata.
- Future GTFS data.

Keep provider IDs separate from Gadiruta's internal primary keys.

Caching policy should reflect data volatility:

### Long-lived

- Stops.
- Locations.
- Lines.
- Operators.

### Medium-lived

- Timetables.
- Route structures.

### Short-lived

- Alerts.
- Dynamic/upcoming information where applicable.

Initial synchronization should remain simple. Prefer management commands plus cron/scheduler before introducing Celery or Redis solely for background synchronization.

---

## Localization

All user-facing frontend strings go through `react-i18next`.

Languages:

- English.
- Spanish.

English is the source/fallback language.

A saved EN/ES preference takes priority over the first supported browser language; otherwise the
UI falls back to English. Storage failures do not prevent switching languages. Bundled resources
cover all interface text, while official place names remain unchanged. Document language, page
title, and fetch timestamps follow the active locale.

---

## Testing boundaries

Normal automated tests should not depend on live CTAN availability.

Use representative saved CTAN fixtures for:

- Integration adapter tests.
- Normalization tests.
- Django API tests.

Live CTAN calls are appropriate during discovery and optionally through explicitly separated integration tests.

---

## Future GTFS boundary

CTAN's GTFS feed should be investigated early but is not part of MVP route planning.

Future routing may use GTFS for:

- Transfers.
- Multi-line journeys.
- Walking transfers.
- Earliest-arrival calculation.
- Full journey planning.

The current CTAN/Django API boundary should not make a future GTFS-backed routing engine difficult to introduce.

---

## Maps

Maps are not part of the MVP.

Coordinates and geometry should still be preserved when provided upstream so a future map layer can be added without redesigning the core transport model.
