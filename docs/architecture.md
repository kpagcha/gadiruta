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

`PlaceProvider` returns normalized provider-scoped population centres with external IDs and labels,
or raises `ProviderError`; the application resolves them to persistent public `Place` values.
`DirectJourneyProvider` accepts two such provider-scoped places plus a date and returns normalized
scheduled services. It deliberately does not expose raw candidate lines, CTAN planner tables, or
provider errors. Implementations own retrieval, normalization, external identifiers, and resource
cleanup. The application owns canonical identity, cache policy, optional departure filtering, and
API behavior.

`transport/providers/wiring.py` is the explicit composition point for each deployment-selected
capability. `GADIRUTA_PLACE_PROVIDER=ctan` and `GADIRUTA_DIRECT_JOURNEY_PROVIDER=ctan` are the
only supported values today. Services call these factories without importing the concrete
integration. API handlers catch `ProviderError` and return application-level errors without
logging provider or database details.

There is no monolithic transport provider, automatic fallback, or multi-provider aggregation. A
future provider can implement one capability without requiring a premature implementation of all
other transport features.

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
required resources, skipping municipality retrieval when there are no centres. `CTANDirectJourneyProvider`
first discovers candidate lines, maps their CTAN IDs to normalized transport modes through the line catalogue,
then fetches each dated line timetable with bounded concurrency.
It fails the complete lookup if any candidate timetable is unavailable, rather than returning a
silently partial result. Its adapter matches origin/destination population-centre groups safely,
extracts only usable rows, and normalizes line code, times, duration, and source note.

Place services map catalogue records to canonical database identities, cache the public catalogue,
and perform local accent-insensitive matching and ranking. Direct-journey services reverse the
active direct provider's canonical crosswalks, cache an unfiltered complete result for an hour, and
apply departure-time filters afterward. `depart_before` is an application-level cutoff: it selects
the complete chronologically ordered earlier portion of that same selected-day catalogue. The
browser reveals that returned segment in four-service visual pages, avoiding a request for each
earlier page. The API explicitly selects public fields and does not interpret provider identity.

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
        components/             # Shared shell and small UI primitives
            AppFooter.tsx
            AppHeader.tsx
            Button.tsx
            date-time-picker/
                calendar.ts
                DateTimePicker.tsx
                TimePicker.tsx
            Icon.tsx
            Panel.tsx
            Skeleton.tsx
        features/
            journey-search/
                calendar.ts
                CompactJourneySearchSummary.tsx
                DirectJourneyResults.tsx
                JourneyDateTimePicker.tsx
                JourneySearchForm.tsx
                JourneyServiceCard.tsx
                PlaceAutocomplete.tsx
                useScrollToResults.ts
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

`HomePage` coordinates URL state, provider queries, automatic submission, and responsive placement. The journey-search
feature owns the editable form, autocomplete, compact mobile summary, and direct-service result presentation. Its thin
date/time adapter supplies journey wording and values to a reusable, feature-neutral picker. Shared components cover
the persistent shell plus repeated visual treatments, retaining native HTML
elements (`button` and `section`) rather than introducing a general-purpose UI library. The shared Tailwind `desktop`
breakpoint is the 850px layout transition used by the shell and journey search.

React Router supplies the homepage and a localized not-found page. Each autocomplete keeps draft
text separate from a confirmed public place identity. TanStack Query shares suggestion results
between fields, debounces requests by 250 ms, and cancels obsolete requests. Suggestions have a
five-minute freshness window and a ten-minute inactive lifetime; failed requests are not automatically
retried, and the error state offers a retry control.
The homepage uses a calendar popover with an optional departure-time input, explicit confirmation,
and a resettable “Now” chip. It writes `from`, `to`, `date`, and optional `depart_after` to the URL
only on a valid submit.
`from` and `to` are readable persistent place slugs, not opaque UUIDs. A reload of that URL queries
direct services and derives the selected labels from the normalized response. Loading stays in the
submit button and a shadcn-style skeleton result card. A successful desktop search puts the editable
search card in the left column and the service list in the right; on mobile the search card collapses
to an actionable route summary. The API clients validate response shape and impose a 25-second
request timeout.

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
does not contact a database or upstream provider. Place search and direct journey search resolve
provider records through PostgreSQL-backed canonical identities on a cache miss. The remaining
resource plans are in `docs/features.md`.

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

Direct journey results use a separate one-hour process-local cache keyed by direct-provider key,
provider-scoped origin/destination IDs, and selected date. The cached value is the full normalized
provider result; time filtering happens per request and does not multiply upstream calls. Empty
candidate discovery is a successful cached result. Provider failures are never cached and no
partial candidate-line response is exposed.

CTAN line metadata has its own one-hour process-local cache keyed to the current integration format.
It maps provider line IDs to transport modes, avoiding a full line-catalogue request for every uncached
journey search. This metadata improves presentation only: an unavailable or unrecognized mode becomes
the normalized `unknown` value without discarding a usable timetable.

The versioned cache key identifies Gadiruta's public catalogue rather than an upstream endpoint.
`CanonicalPlace` holds immutable public UUIDs, current labels, and a stable human-readable URL
slug. `ProviderPlaceReference` maps a provider key plus external ID to that identity. A record
without a crosswalk receives a new UUID4 identity, whether it comes from CTAN or a future provider.
Its initial slug uses the normalized place name; collisions use municipality context and then a
stored numeric suffix. Slugs do not change during display-label refreshes. Records are never
matched by labels automatically, so deliberate crosswalks can be added later without risking false
matches.

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
cover all interface text, while official place names remain unchanged. Document language and page
title follow the active locale.

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
