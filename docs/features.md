# Feature Inventory

This file tracks current product capability and the next major milestones. Git history records implementation details.

## Backend foundation

**Status: Implemented**

- [x] Django + PostgreSQL backend with environment-based settings.
- [x] Versioned Django Ninja API and liveness endpoint.
- [x] Generated OpenAPI with Scalar UI and global data attribution.
- [x] pytest, Ruff, mypy, locked Python dependencies, and shared Git hooks.
- [x] Canonical place identities and provider-reference crosswalks.

## Place search

**Status: Implemented**

- [x] Cádiz-area population-centre catalogue.
- [x] Municipality context.
- [x] Accent/case-insensitive ranked search.
- [x] Stable Gadiruta place IDs/slugs.
- [x] Origin/destination autocomplete and swap.
- [x] Loading, empty, retryable-error, and keyboard-accessible states.
- [x] Provider-neutral place boundary with CTAN REST as the current source.

## Direct journey search

**Status: Initial CTAN REST implementation exists; data source scheduled for replacement**

- [x] Date selection.
- [x] Optional departure-time filter.
- [x] Automatic search after selecting both places.
- [x] Journey result cards and responsive result layout.
- [x] Search state in the URL and restoration on reload.
- [x] Provider-neutral direct-journey service boundary.
- [ ] Replace CTAN REST timetable lookup with locally imported GTFS data.

The current REST implementation has calendar/date limitations and should not be expanded as the long-term timetable model.

## GTFS migration

**Status: GTFS data and CTAN place-to-stop links imported; local direct-journey lookup next**

- [x] Download and structurally validate the CTAN unified GTFS feed with a read-only inspection
  command and deterministic synthetic-feed tests.
- [x] Persist versioned GTFS dataset metadata and normalized static transit tables, with active-
  dataset protection, direct-journey query indexes, and future place-to-stop links.
- [x] Import agencies, stops, routes, trips, stop times, calendars, exceptions, and shapes.
- [x] Activate imports atomically and retain the previous valid dataset on failure.
- [x] Establish CTAN `Place` to GTFS-stop associations using the verified physical-stop ID crosswalk.
- [ ] Reproduce existing direct-journey searches from local GTFS data.
- [ ] Verify holiday/date handling through `calendar.txt` and `calendar_dates.txt`.
- [ ] Verify overnight/past-midnight service handling.
- [x] Audit the current unified feed's mode/agency coverage: it has the nine CTAN consortia and
  bus/ferry routes, but no rail or Trambahía routes.
- [ ] Identify additional feeds if CTAN GTFS coverage is incomplete.
- [ ] Retire unnecessary REST timetable dependencies after validation.

## Lines

**Status: Planned**

- [ ] Search/browse lines.
- [ ] Line detail with operator and directions.
- [ ] Ordered stops.
- [ ] Timetable/schedule.
- [ ] Relevant alerts.
- [ ] Preserve route geometry.

GTFS should supply the core line/route/trip data.

## Stops and locations

**Status: Population-centre search implemented; physical-stop features planned**

- [x] Search/select population centres.
- [ ] Place-to-GTFS-stop mapping.
- [ ] Physical stop detail.
- [ ] Serving lines.
- [ ] Upcoming scheduled services.
- [ ] Direction/destination.
- [ ] Relevant alerts.

## Alerts

**Status: Planned / source to verify**

- [ ] Identify the authoritative alert source.
- [ ] Associate alerts with affected lines/stops where possible.
- [ ] Surface relevant alerts in journeys and line/stop views.

Investigate CTAN REST and any available GTFS-Realtime source before choosing the implementation.

## Favorites and history

**Status: Planned**

- [ ] Recent searches in `localStorage`.
- [ ] Favorite journeys.
- [ ] Favorite lines/stops if useful.

## Localization

**Status: Implemented for current UI**

- [x] English and Spanish.
- [x] English fallback.
- [x] Browser-locale detection.
- [x] Persisted EN/ES selection when storage is available.
- [x] User-facing component strings use the translation system.

## Appearance and accessibility

**Status: Implemented for the current search flow**

- [x] Mobile-first responsive layout.
- [x] Light/dark theme with persisted preference.
- [x] Keyboard-usable autocomplete.
- [x] Accessible labels, focus states, skip link, and live status announcements.

## PWA / installability

**Status: High-priority post-MVP**

- [ ] Web app manifest and application icons.
- [ ] Service worker and offline app shell.
- [ ] Deliberate caching/freshness behavior for recently viewed transport data.
- [ ] Predictable update detection and activation.

## Maps

**Status: Deferred beyond MVP**

- [ ] Interactive map.
- [ ] Stops and line geometry.
- [ ] Journey-leg visualization.
- [ ] Nearby transport.

## Multi-leg routing

**Status: Deferred beyond MVP**

- [ ] Transfer journeys.
- [ ] Walking transfers.
- [ ] Earliest-arrival routing.
- [ ] Mature GTFS routing engine integration.

Do not implement a custom general-purpose routing engine.

## Authentication

**Status: Out of MVP**

- [ ] Accounts.
- [ ] Server-side favorites/history.
- [ ] User synchronization.
