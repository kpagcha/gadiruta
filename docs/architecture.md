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
 PlaceProvider capability
       ↓
  CTAN integration
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
    providers/
        base.py
        wiring.py
    integrations/
        ctan/
            client.py
            schemas.py
            adapters.py
            provider.py
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
- Coordinate normalized provider data through capability-specific contracts.
- Own catalogue caching, freshness timestamps, and local search ranking.

### Provider capability boundary

`PlaceProvider` in `transport/providers/base.py` defines only the implemented place capability.
It returns normalized provider-scoped records with external IDs and labels, or raises
`ProviderError`; the application resolves them to persistent public `Place` values. Implementations
own retrieval, normalization, external identifiers, and resource cleanup. The application owns
canonical identity, caching, and search behavior.

`transport/providers/wiring.py` is the explicit composition point for one deployment-selected
provider. `GADIRUTA_PLACE_PROVIDER=ctan` is the only supported value today. Services call this
factory without importing the concrete integration. API handlers catch `ProviderError` and return
application-level errors without logging provider or database details.

Add other capability contracts only when needed; there is no monolithic transport provider,
automatic fallback, or multi-provider aggregation. Direct-journey work will add its own contract
when that feature starts.

### CTAN integration layer

- Perform upstream HTTP requests.
- Parse and validate CTAN responses.
- Normalize provider-specific fields.
- Isolate CTAN-specific identifiers and quirks.
- Join centre/municipality records and retain CTAN external IDs.
- Translate CTAN exceptions to `ProviderError` at the capability implementation boundary.

Raw CTAN payloads must not become Gadiruta's public API contract.

The HTTP client validates provider records with Pydantic. CTAN identifiers, relationships, and zone
fields remain in integration records. The adapter produces immutable provider records containing an
external ID, name, and optional municipality label. `CTANPlaceProvider` fetches and joins the
required resources, skipping municipality retrieval when there are no centres. Place services map
these records to canonical database identities, cache the public catalogue, and perform local
accent-insensitive matching and ranking. The API explicitly selects public fields and does not
interpret provider identity.

---

## Frontend

Stack:

- React 19.
- TypeScript.
- Vite.
- Tailwind CSS 4 through the Vite plugin.
- Lucide React for interface icons.
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
        theme.ts
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
- Token-based light/dark presentation with a persisted theme preference.

Tailwind utility classes provide component-level layout and visual styling. The shared stylesheet keeps only global
font/base/accessibility rules, design tokens, and small custom CSS that is clearer outside JSX. Lucide React supplies
the shared interface icon set; icons remain decorative unless their surrounding control provides an accessible name.
Semantic theme tokens are overridden on the document's `data-theme` attribute. The first visit follows the browser's
system preference; the header toggle persists an explicit light/dark choice in `localStorage`. A small head bootstrap
applies the initial attribute before the React bundle loads to avoid a light-theme flash.

React Router supplies the homepage and a localized not-found page. Each autocomplete keeps draft
text separate from a confirmed public place identity. TanStack Query shares suggestion results
between fields, debounces requests by 250 ms, and cancels obsolete requests. Suggestions have a
five-minute freshness window and a ten-minute inactive lifetime; failed requests are not automatically
retried, and the error state offers a retry control.
The API client validates response shape and imposes a 25-second request timeout.

Browser requests use relative `/api/v1/` URLs. Vite proxies `/api/` to Django on port 8000 during
development and local build preview, so no cross-origin API configuration is needed. Production
hosting is not configured: it will need same-origin API forwarding and SPA fallback for UI routes.

### Post-MVP PWA boundary

PWA support is the preferred post-MVP extension of the existing React + Vite frontend. It should remain a web-first
application rather than creating a second near-term mobile frontend. The planned PWA boundary includes:

- A manifest and platform-appropriate icons for installation on Android and iOS.
- A service worker that provides a reliable offline application shell.
- Carefully scoped caching for recently viewed transport data, preserving freshness metadata and making stale data
  visible to users.
- Deliberate update detection and service-worker activation behavior so users do not remain on an unexpectedly old
  application shell.

The PWA must continue to use Gadiruta's Django API for provider-backed data. Offline caching is an enhancement for
recently available data, not permission to expose raw CTAN responses or silently present data as current. This work
starts only after the first-version journey, schedule, line, stop, alert, localization, and responsive milestones are
complete.

React Native/Expo is a later fallback, not a parallel architecture target. Reconsider a native app only if genuinely
native requirements emerge that the browser/PWA platform cannot satisfy adequately.

---

## API boundary

The frontend calls Gadiruta's Django API, mounted at `/api/v1/`. Application liveness deliberately
does not contact a database or upstream provider. Place search uses the configured place provider on cache
misses and does not require a database. The remaining resource plans are in `docs/features.md`.

Django Ninja/OpenAPI is the canonical endpoint-level reference. Source attribution and the
independence disclaimer appear once in the top-level API description, also displayed by Scalar.
Endpoint descriptions focus on their own behavior. The web application retains its global footer
attribution and disclaimer.

---

## Persistence and caching

The population-centre catalogue uses Django's default local-memory cache with a one-hour TTL,
shared across search queries within each process. On a cache miss, a successful provider fetch
upserts canonical places and provider-reference crosswalks in PostgreSQL before the public
catalogue is cached. The timestamp reflects the completed fetch, not the upstream publication
time. A valid empty catalogue is cacheable; failures are not. An unexpired catalogue can serve
requests during provider outages. There is no stale-on-error fallback, background refresh, or
shared multi-worker cache yet.

The versioned cache key identifies Gadiruta's public catalogue rather than an upstream endpoint.
`CanonicalPlace` holds immutable public UUIDs and current labels. `ProviderPlaceReference` maps a
provider key plus external ID to that identity. A record without a crosswalk receives a new UUID4
identity, whether it comes from CTAN or a future provider. Records are never matched by labels
automatically, so deliberate crosswalks can be added later without risking false matches.

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

Normal automated tests should not depend on live provider availability.

Service/API boundary tests use a small structural `PlaceProvider` stub with provider-scoped records
and neutral errors, without CTAN HTTP. PostgreSQL-backed tests cover canonical UUID assignment,
reference reuse, label refreshes, and unmapped-provider behavior. They also cover ranking, caching,
empty results, short queries, and safe error responses independently of the current integration.

Saved CTAN fixtures and mock HTTP transports cover the client, adapters, concrete provider, and
end-to-end API regressions. Provider tests also verify error translation and HTTP resource cleanup.

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

Capability-specific provider boundaries should allow a future GTFS-backed routing implementation
without requiring it to supply unrelated capabilities or exposing its format through Gadiruta's API.

---

## Maps

Maps are not part of the MVP.

Coordinates and geometry should still be preserved when provided upstream so a future map layer can be added without redesigning the core transport model.
