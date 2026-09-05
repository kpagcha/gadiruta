# Feature Inventory

This document tracks Gadiruta's **current functional capabilities**.

Keep it concise. Update it when features are added, removed, completed, substantially changed, or explicitly deferred.

Do not use this file as a development diary. Git history records implementation changes.

---

## Backend foundation

Status: Implemented

- [x] Existing Django project configured for PostgreSQL and environment-based settings.
- [x] Versioned Django Ninja API with typed application liveness response.
- [x] Generated OpenAPI schema and interactive API documentation.
- [x] Locked dependencies, pytest, Ruff lint/format checks, and mypy type checks.

Transport integration and the React frontend are not implemented yet. The next milestone is to
verify CTAN population-centre responses, save representative fixtures, and expose normalized place
search through the API.

---

## Journey search

Status: Planned

- [ ] Origin autocomplete.
- [ ] Destination autocomplete.
- [ ] Swap origin/destination.
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

Status: Planned

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

Status: Planned

- [ ] English UI.
- [ ] Spanish UI.
- [ ] English fallback language.
- [ ] Browser locale detection.
- [ ] EN / ES language switcher.
- [ ] No unlocalized user-facing strings in components.

---

## Responsive/accessibility

Status: Planned

- [ ] Mobile-first responsive layout.
- [ ] Keyboard-usable journey search.
- [ ] Accessible labels for controls.
- [ ] Appropriate focus states.
- [ ] Loading/error/empty states readable by assistive technology where appropriate.

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

Status: Foundation implemented; transport resources planned

The versioned API currently exposes application liveness and generated documentation. Liveness
does not imply PostgreSQL or CTAN availability. See `docs/development.md` for local URLs.

Potential resources:

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

These are provisional until CTAN discovery confirms which resources and mappings are reliable.

Django Ninja/OpenAPI is the canonical endpoint-level API reference.
