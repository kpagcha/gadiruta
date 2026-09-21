# Architecture

## Overview

Gadiruta is a single repository with a React frontend and Django API.

```text
Browser / React
       ↓
   Django API
       ↓
Transport domain/services
       ↓
Local normalized transit data
       ↑
 scheduled GTFS import
       ↑
   CTAN GTFS feed
```

A small CTAN REST integration may remain for data GTFS does not provide, especially population-centre metadata and possibly alerts or supplementary metadata.

The frontend must never depend directly on CTAN REST or GTFS shapes.

## Repository boundaries

The repository currently keeps the Django project at the root and the frontend under `frontend/`:

```text
gadiruta/
    gadiruta/      # Django settings, root API and URLs
    transport/     # Transport domain, services, providers and integrations
    frontend/      # React application
    tests/
    docs/
```

Backend and frontend are versioned together but run independently in development.

## Backend layers

### API layer

Django Ninja exposes the versioned Gadiruta API and generated OpenAPI documentation. API handlers validate requests, call application services, and return stable public schemas.

Endpoint-level contracts belong in OpenAPI, not duplicated in these docs.

### Domain and service layer

The transport domain owns provider-neutral concepts and application behavior. Services coordinate place search, direct-journey lookup, caching where useful, and persistence without exposing upstream-specific identifiers to API consumers.

### Provider/integration layer

Provider-specific code belongs behind narrow capability boundaries. CTAN REST and GTFS parsing/import logic may use provider IDs internally, but services and public schemas should operate on Gadiruta identities and normalized domain values.

Do not introduce a monolithic transport-provider abstraction merely to unify unrelated capabilities.

## Places and stops

`Place` is a Gadiruta search/grouping concept above physical transit stops.

A place may correspond to many GTFS stops:

```text
Place: Cádiz
  ├─ GTFS stop A
  ├─ GTFS stop B
  └─ GTFS stop C
```

This lets users search by population centre while direct-journey logic works over real stop sequences.

Current place discovery is based on CTAN `núcleos`/municipalities and persists canonical Gadiruta identities plus provider-reference crosswalks. Longer term, the place hierarchy may become fully local if a reliable authoritative locality dataset and stop-to-place mapping are available.

Labels are presentation data, not identity. Upstream IDs must remain separate from Gadiruta primary/public identities.

## GTFS as the static transit source

The immediate target is for imported GTFS to be authoritative for:

- agencies/operators;
- stops;
- routes/lines;
- trips;
- stop times;
- regular service calendars;
- date-specific calendar exceptions;
- shapes;
- direct-journey lookup.

The application should not call CTAN timetable endpoints at request time once this migration is complete.

### Import flow

```text
CTAN GTFS feed
      ↓
download candidate feed
      ↓
validate structure and required relationships
      ↓
import candidate dataset
      ↓
activate atomically
      ↓
serve queries from local data
```

A failed download or invalid import must leave the previous active dataset usable. Start with a Django management command plus cron/scheduler; do not add Celery or Redis solely for this job.

The feed is expected to refresh regularly, probably daily. Download optimization with `ETag`, `Last-Modified`, or hashes can be added later.

The current `inspect_gtfs` management command is a non-mutating first step: it downloads or reads a
local archive, validates the required tables and fields, and reports a checksum and coverage summary.
Persistent candidate import and atomic activation are the next implementation steps.

## Direct-journey lookup

For a requested origin place, destination place, date, and optional departure time:

1. Resolve each place to its associated GTFS stops.
2. Find trips containing an origin stop before a destination stop.
3. Keep only trips whose `service_id` is active on the requested date according to `calendar.txt` plus `calendar_dates.txt`.
4. Read departure/arrival times from `stop_times.txt`.
5. Apply `depart_after` / `depart_before` filtering locally.
6. Return normalized journey results ordered by departure.

This is direct-trip matching, not general route planning.

Times and service-day handling must preserve valid GTFS overnight semantics, including times beyond `24:00:00` if present.

## Remaining CTAN REST role

CTAN REST is no longer the intended primary schedule/network source. Keep a REST dependency only when GTFS does not provide the capability adequately.

Likely candidates to verify:

- population-centre and municipality discovery;
- stop-to-`núcleo` association, if reliably exposed;
- service alerts/notices;
- useful provider-specific metadata not present in GTFS.

Do not keep a REST dependency merely because code already exists.

## Persistence

PostgreSQL stores durable application identity and is the intended home for imported/normalized transit data.

At minimum, persistence needs to support:

- canonical places and provider references;
- place-to-stop associations;
- active GTFS dataset metadata;
- imported agencies, stops, routes, trips, stop times, calendars, exceptions, and shapes as needed by queries.

Exact table design belongs to implementation work, not this document.

Imports should make dataset freshness and provenance inspectable.

## Frontend

The frontend uses React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Lucide React, and react-i18next.

Its responsibilities are interaction, URL/search state, request caching, responsive presentation, localization, and local browser preferences. It communicates only with Gadiruta's API using relative `/api/v1/` URLs.

English and Spanish UI strings are bundled with react-i18next. Theme and language preferences may be persisted in `localStorage`.

## Testing boundaries

Normal automated tests must not depend on live CTAN availability.

Use:

- provider-neutral service/API tests for application behavior;
- captured REST fixtures for remaining CTAN REST adapters;
- small representative GTFS fixture feeds for importer and journey-query tests;
- database tests for canonical identities, crosswalks, imports, activation, and direct-journey queries.

Live upstream calls belong only in explicit discovery or integration checks.

## Future routing

GTFS migration is deliberately compatible with later multi-leg routing, but the MVP must not grow its own general-purpose routing algorithm.

Future architecture:

```text
GTFS feed(s)
    ↓
routing engine (for example OpenTripPlanner)
    ↓
Gadiruta normalized journey API
    ↓
frontend
```

Additional GTFS feeds can be introduced if CTAN's feed does not cover all Cádiz modes required by the product.

## Maps and PWA

Maps are outside the MVP; preserve stop coordinates and route shapes so they can be added later without redesigning the transport model.

PWA support is the preferred post-MVP mobile extension of the existing React application. React Native/Expo is not a parallel near-term architecture target.
