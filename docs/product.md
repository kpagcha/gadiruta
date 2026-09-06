# Gadiruta Product Definition

## Goal

Build an initial web application inspired conceptually by Rome2Rio, focused specifically on public transport in the
Cádiz area.

The first version will **not attempt full multi-leg route planning**.

Instead, it should make the official CTAN transport data significantly easier and faster to use for:

- Finding direct public transport between two places.
- Checking upcoming services and schedules.
- Exploring transport lines.
- Exploring stops / population centres.
- Seeing relevant service notices.

Primary upstream data source:

https://api.ctan.es/doc/

For Cádiz, use the Bahía de Cádiz consortium (`2`).

The application must be structured so other transport sources and proper route planning can be added later.

---

## Product principles

The app should feel:

- Extremely simple.
- Fast.
- Mobile-first.
- Friendly rather than bureaucratic.
- Visually spacious.
- Immediately understandable without instructions.

Use https://clicks.coffee/ as the main aesthetic reference.

Do not copy it literally. Take inspiration from:

- Strong typography.
- Lots of whitespace.
- Restrained use of color.
- Large, comfortable form controls.
- Rounded cards and controls.
- Very little visual clutter.
- Clear visual hierarchy.
- One obvious primary task per screen.

Avoid making it look like a traditional transit authority website or a dense dashboard.

---

## Language

The project itself is written in English:

- Code.
- Variables.
- Comments.
- Documentation.
- Git commits.
- API field names.

The UI must support:

- English.
- Spanish.

English is the source/fallback translation language.

Spanish translations must be included from the beginning.

Do not scatter user-facing text throughout React components.

All UI strings should use the translation system.

Detect the user's browser locale initially and provide a simple EN / ES language selector.

---

# MVP experience

## Home

The primary interaction should dominate the page.

Conceptually:

```text
Where are you going?

[ From                         ]
[ To                           ]

          ⇅

[ Today / Date ] [ Time ]

[ Find transport ]
```

Origin and destination should use autocomplete backed by known CTAN locations/stops rather than free-form arbitrary
street addresses.

Include an easy swap-origin/destination action.

Below the main search, optionally show:

- Recent searches.
- Favorite journeys.
- A subtle link to browse lines.

Do not overload the home page.

---

## Direct journey search

This is the main MVP feature.

Given:

- Origin.
- Destination.
- Date.
- Optional departure time.

Find direct public transport services between them using CTAN data.

No transfers should be calculated in this version.

If there is no direct service, clearly communicate:

```text
No direct service found.
Routes requiring transfers aren't supported yet.
```

Do not imply that no possible public transport journey exists.

---

## Journey results

Each result should communicate as much of the following as the source data reliably allows:

- Departure time.
- Arrival time.
- Duration.
- Transport mode.
- Line.
- Operator.
- Origin stop/location.
- Destination stop/location.
- Relevant service warnings.
- Whether the service runs on the selected date.

Make departure time and destination the strongest visual elements.

Results should be easy to scan on a phone.

Allow changing:

- Date.
- Time.
- Direction.

without forcing the user back to the home page.

Search state should be represented in the URL so searches can be shared and bookmarked.

---

## Lines

Provide a searchable list of transport lines.

Line detail should show:

- Line number/name.
- Operator.
- Direction (s).
- Stops in order.
- Schedule/timetable.
- Relevant alerts/notices.

If geographic route geometry is readily available, retain it in the data model/API even if the MVP does not yet render a
map.

---

## Stops / locations

Allow users to search for or open a stop/location.

Where supported by CTAN, show:

- Lines serving it.
- Upcoming services.
- Direction / destination.
- Associated alerts.

---

## Alerts

CTAN service news/notices should be exposed where relevant.

An alert concerning a line should appear on:

- That line's page.
- Journey results using that line.

Avoid making users separately inspect an alerts page to discover that their journey is affected.

---

## Favorites and recent searches

No authentication is required for the MVP.

Store in browser localStorage:

- Recent origin/destination searches.
- Favorite journeys.
- Favorite lines/stops if implemented.

Design the storage format so it can later be migrated to server-side user accounts.

---

# Data and integration principles

## Own API

The frontend should use Gadiruta's own stable resource model rather than CTAN's raw API.

Potential endpoint shape:

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

These endpoints are provisional. Do not implement them blindly.

Inspect the actual CTAN API and determine which resources can be populated reliably.

Gadiruta's generated Django Ninja/OpenAPI documentation is the canonical endpoint-level reference.

---

## CTAN integration

Before building substantial behavior around the upstream provider, determine:

1. Relevant endpoints.
2. Required query parameters.
3. IDs and relationships between:
    - consortium
    - location / population centre
    - stop
    - line
    - route/direction
    - trip/service
    - timetable/calendar
    - operator
4. Date/calendar representation.
5. Transport modes.
6. Missing/null/inconsistent data.
7. Error responses.
8. Whether requests support Spanish/English data.
9. Refresh frequency.
10. Any useful endpoints not initially obvious.

Representative real responses should be captured as fixtures for tests.

The application must tolerate:

- Empty arrays.
- Missing optional fields.
- Upstream HTTP errors.
- Timeouts.
- Unexpected or inconsistent records.

Never crash the frontend because CTAN returned incomplete data.

---

## Caching

CTAN should not need to be contacted repeatedly for data that rarely changes.

Likely cache classes:

### Long-lived

- Stops.
- Locations.
- Lines.
- Operators.

### Medium-lived

- Timetables.
- Route structures.

### Short-lived

- Service alerts.
- Dynamic/upcoming information where applicable.

For the initial implementation, keep infrastructure simple.

PostgreSQL may be used for persistent normalized/cached data.

Do not introduce Celery solely for the MVP. Periodic synchronization can initially use a Django management command plus
cron/scheduler if needed.

Architect things so Redis or background jobs can be added later without redesigning the CTAN integration.

---

## PostgreSQL

Even though the MVP is mainly read-only, PostgreSQL can eventually hold:

- Normalized CTAN entities.
- Cached schedules.
- Location aliases/search terms.
- Synchronization metadata.
- User favorites if accounts are introduced.
- Additional transport providers.
- Imported GTFS data.

Keep upstream IDs separate from internal IDs.

Do not make CTAN identifiers the application's primary keys by default.

---

# Maps

Maps are **not required for the first MVP**.

Preserve coordinates and route geometry when CTAN provides them.

A later version can add MapLibre/Leaflet-based visualization for:

- Stops.
- Line routes.
- Journey legs.
- Nearby transport.

Do not let map implementation delay the core search experience.

---

# Data attribution

This is an independent application and must clearly identify its source.

Include a small footer/data attribution based on:

```text
Information provided by the Portal de Datos Abiertos de la Red de Consorcios de Transporte de Andalucía.
```

Also communicate that the application is independent and is not an official CTAN/Junta de Andalucía service.

Do not imply endorsement or affiliation.

Where useful, display when transport information was last fetched/updated.

---

# Explicitly outside MVP

Do **not** initially implement:

- Transfer route calculation.
- Arbitrary street-address routing.
- Walking directions.
- Driving.
- Flights.
- Accounts/authentication.
- Payments.
- Native mobile apps (including React Native/Expo); revisit them only if genuinely native requirements remain after
  the PWA route has been evaluated.
- Push notifications.
- Complex map functionality.
- Full Andalusia coverage.
- Custom routing algorithms.

Focus on Cádiz and make the basic experience excellent first.

---

# Future phases

## Phase 2: post-MVP priorities

After the first-version milestones are complete and the core workflow is polished, prioritize PWA support as the next
major product step. Keep Gadiruta web-first by extending the existing React + Vite application so it can be installed
and feel app-like on Android and iOS.

PWA work should cover, as appropriate:

- A web app manifest and platform-appropriate application icons.
- A service worker and reliable offline app shell.
- Sensible caching of recently viewed transport data, with clear freshness and stale-data behavior.
- Predictable update detection, user messaging, and service-worker activation.

The token-based dark theme is already implemented as a small cross-cutting frontend enhancement, with system-preference
support and an explicit user toggle. It does not change the product's web-first direction or the priority of PWA as the
next major post-MVP feature.

After that PWA foundation, prioritize:

- Interactive map.
- Nearby stops.
- Fares.
- Better favorites.

React Native/Expo remains a later option, not a parallel near-term frontend. Reconsider it only if requirements emerge
that the web platform and PWA cannot satisfy well, such as genuinely native capabilities or constraints.

## Phase 3

GTFS-powered route calculation:

```text
A → bus → transfer → train → B
```

Consider a mature transit routing engine rather than building the algorithm from scratch.

## Phase 4

Additional datasets/providers:

- Municipal transport not covered by CTAN.
- Renfe or other rail data where necessary.
- Ferry providers.
- Other Andalusian transport consortia.
- Walking routing/geocoding.

At that point the product can evolve toward a true Cádiz-focused Rome2Rio-style journey planner.

---

# First implementation milestone

The first usable milestone should allow:

1. Open the homepage.
2. Search for Cádiz-area origin and destination locations.
3. Choose today or another date.
4. Find direct services between those locations.
5. See upcoming departure options clearly.
6. Open the corresponding line.
7. Inspect its stops and timetable.
8. Switch between English and Spanish.
9. Use the application comfortably on both mobile and desktop.

Before expanding the feature set, make this workflow polished, fast, and reliable.
