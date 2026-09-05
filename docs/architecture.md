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

Initial intended structure:

```text
gadiruta/
    AGENTS.md
    README.md
    backend/
    frontend/
    docs/
```

Backend and frontend should be independently runnable but versioned together.

---

## Backend

Stack:

- Python.
- Django 6.1.1.
- Django Ninja.
- PostgreSQL.
- httpx.
- pytest / pytest-django.

Suggested organization:

```text
backend/
    config/
    transport/
        api.py
        schemas.py
        services/
            journey_search.py
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

---

## Frontend

Stack:

- React 19.
- TypeScript.
- Vite.
- React Router.
- TanStack Query.
- react-i18next.

Suggested organization:

```text
frontend/
    src/
        api/
        components/
        features/
            journey-search/
            lines/
            stops/
            alerts/
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
- localStorage-based recent/favorite state for MVP.

---

## API boundary

The frontend calls Gadiruta's Django API.

Potential initial endpoints:

```text
GET /api/v1/places?q=
GET /api/v1/journeys/direct
GET /api/v1/lines
GET /api/v1/lines/{id}
GET /api/v1/lines/{id}/schedule
GET /api/v1/stops/{id}
GET /api/v1/stops/{id}/departures
GET /api/v1/alerts
```

These are provisional until CTAN discovery verifies the required mappings.

Django Ninja/OpenAPI is the canonical endpoint-level reference.

---

## Persistence and caching

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

Browser locale may determine the initial language, with an explicit EN/ES switcher available.

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
