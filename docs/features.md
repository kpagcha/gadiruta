# Feature Inventory

This document tracks Gadiruta's **current functional capabilities**.

Keep it concise. Update it when features are added, removed, completed, substantially changed, or explicitly deferred.

Do not use this file as a development diary. Git history records implementation changes.

---

## Backend foundation

Status: Implemented

- [x] Existing Django project configured for PostgreSQL and environment-based settings.
- [x] Versioned Django Ninja API with typed application liveness response.
- [x] Generated OpenAPI schema and interactive Scalar API documentation.
- [x] Locked dependencies, pytest, Ruff lint/format checks, and mypy type checks.

The CTAN place-search backend and English/Spanish place-selection homepage are implemented.
Direct-service lookup is the next functional slice; it requires upstream timetable/calendar
discovery before implementation. Automated frontend interaction tests (such as autocomplete,
swapping, and language-switching tests) are deferred as low priority and do not block current
milestones. Frontend verification uses static checks and manual browser checks for now.

---

## Journey search

Status: Place selection implemented; journey lookup planned

- [x] Origin autocomplete.
- [x] Destination autocomplete.
- [x] Swap origin/destination, including partially typed input.
- [ ] Date selection.
- [ ] Time selection/filtering.
- [ ] Direct service lookup.
- [ ] Journey result cards.
- [ ] Loading state.
- [ ] Empty state.
- [ ] Error state.
- [ ] Search state in URL.
- [ ] Shareable/bookmarkable searches.

Notes:

- MVP supports direct journeys only.
- Routes requiring transfers must not be presented as impossible; they are simply unsupported in the MVP.
- Place suggestions support loading, empty, and retryable error states. Typing clears any previous
  selection; users must select a suggestion to confirm a place. Choosing the same origin and
  destination displays a warning. The homepage explicitly says journey search is not available yet.

---

## Lines

Status: Planned

- [ ] Search/browse lines.
- [ ] Line detail.
- [ ] Operator.
- [ ] Directions.
- [ ] Ordered stops.
- [ ] Timetable/schedule.
- [ ] Relevant alerts.
- [ ] Preserve route geometry when available.

---

## Stops / locations

Status: Population-centre search API and autocomplete implemented; detail pages and physical stops planned

- [x] Search Cádiz population centres by name or municipality, ignoring case and accents.
- [x] Ranked, limited results with stable Gadiruta IDs and optional municipality names.
- [x] One-hour catalogue cache and fetch timestamps.
- [x] Validated CTAN responses, saved fixtures, and offline error/timeout/cache tests.
- [x] Distinguish empty results from unavailable provider data.
- [x] Select population centres in the homepage autocomplete, with municipality and fetch timestamp.
- [ ] Search/open a stop or population centre.
- [ ] Show serving lines.
- [ ] Show upcoming services where supported.
- [ ] Show direction/destination.
- [ ] Show relevant alerts.

---

## Alerts

Status: Planned

- [ ] Retrieve CTAN notices/alerts.
- [ ] Associate alerts with affected lines where possible.
- [ ] Surface relevant alerts in journey results.
- [ ] Surface relevant alerts on line pages.

---

## Favorites and history

Status: Planned

- [ ] Recent searches in localStorage.
- [ ] Favorite journeys in localStorage.
- [ ] Favorite lines/stops if useful.
- [ ] Storage format designed for possible future account migration.

---

## Localization

Status: Implemented for the current homepage and not-found page

- [x] English UI.
- [x] Spanish UI.
- [x] English fallback language.
- [x] Browser locale detection.
- [x] EN / ES language switcher with a saved local preference when storage is available.
- [x] No unlocalized user-facing strings in components.

---

## PWA / installability

Status: High-priority post-MVP feature; not implemented

The preferred post-MVP mobile experience is an installable enhancement of the existing React + Vite web application.
It should be planned after the first-version journey, schedule, line, stop, alert, localization, and responsive
milestones are complete.

- [ ] Web app manifest and install metadata.
- [ ] Application icons suitable for Android and iOS installation.
- [ ] Service worker and offline app shell.
- [ ] Sensible caching of recently viewed transport data, with explicit freshness and stale-data handling.
- [ ] Predictable update detection, messaging, and activation behavior.

React Native/Expo is not planned as a parallel frontend. Reconsider a native implementation only if genuinely native
requirements emerge that the web app and PWA cannot satisfy well.

---

## Appearance

Status: Dark theme planned post-MVP

- [ ] Dark theme with system-preference support and an explicit user toggle.
- [ ] Preserve accessible contrast across both themes.

---

## Responsive/accessibility

Status: Implemented for place selection; broader journey flow planned

- [x] Mobile-first responsive layout.
- [x] Keyboard-usable place selection (arrow keys, Enter, Escape, and Tab).
- [x] Accessible labels for controls and a skip-to-content link.
- [x] Appropriate focus states.
- [x] Live announcements for suggestion loading/error/empty states and selection changes.

---

## Maps

Status: Deferred beyond MVP

- [ ] Interactive map.
- [ ] Stops on map.
- [ ] Line route visualization.
- [ ] Journey leg visualization.
- [ ] Nearby transport.

Notes:

- Preserve coordinates/geometry in the data model when CTAN exposes them even before maps are implemented.

---

## Multi-leg routing

Status: Deferred beyond MVP

- [ ] Transfer journeys.
- [ ] Walking transfers.
- [ ] Earliest-arrival routing.
- [ ] GTFS-powered journey planning.

---

## Authentication

Status: Out of MVP

- [ ] Accounts.
- [ ] Server-side favorites.
- [ ] User synchronization.

---

## API

Status: Liveness and place search implemented; other transport resources planned

The versioned API exposes application liveness, population-centre search, and generated
documentation. Liveness does not imply PostgreSQL or CTAN availability. See `docs/development.md`
for local URLs. Place search uses the default per-process cache, not persistent storage; cold or
expired-cache requests return a stable unavailability response if CTAN cannot supply usable data.

Remaining potential resources:

```text
GET /api/v1/journeys/direct
GET /api/v1/lines
GET /api/v1/lines/{id}
GET /api/v1/lines/{id}/schedule
GET /api/v1/stops/{id}
GET /api/v1/stops/{id}/departures
GET /api/v1/alerts
```

These are provisional until CTAN discovery confirms which resources and mappings are reliable.

Django Ninja/OpenAPI is the canonical endpoint-level API reference.
