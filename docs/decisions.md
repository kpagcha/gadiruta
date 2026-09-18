# Decisions

This file is a lightweight record of significant architectural and product decisions.

Keep entries concise.

Do not record trivial coding choices.

Suggested format:

```text
## YYYY-MM-DD — Decision title

Context:
...

Decision:
...

Why:
...

Consequences:
...
```

---

## Initial decisions

### Single repository for backend and frontend

Context:

Gadiruta contains a Django backend and React frontend that are developed together.

Decision:

Use a single Git repository / monorepo.

Why:

- The product is small enough that separate repositories would add unnecessary coordination overhead.
- Backend and frontend changes will often form one vertical feature slice.
- Shared Git history makes iterative agent development easier to review.

Consequences:

- Backend and frontend remain independently runnable.
- They are versioned and documented together.

---

### Frontend uses Gadiruta's API, not CTAN directly

Context:

CTAN is an external upstream provider whose response formats and availability are outside Gadiruta's control.

Decision:

All browser data access goes through the Django API.

Why:

- Isolates provider-specific behavior.
- Allows normalization and caching.
- Avoids coupling React components to CTAN.
- Makes future data providers and GTFS routing easier to introduce.
- Provides one stable application API contract.

Consequences:

- CTAN HTTP logic belongs behind a dedicated integration layer.
- Raw CTAN payloads must not define public frontend schemas.

---

### Django Ninja provides the canonical API reference

Context:

Manually maintained endpoint documentation easily becomes stale.

Decision:

Use Django Ninja's generated OpenAPI schema and interactive docs as the canonical endpoint-level reference.

Why:

- Documentation remains tied to actual route definitions and schemas.
- Typed request/response contracts reduce duplication.
- Docstrings/descriptions can enrich generated docs without creating a second manual reference.

Consequences:

- `docs/` should explain architecture and behavior, not duplicate every endpoint schema.

---

### English source language with Spanish UI support

Context:

The project codebase is maintained in English, while the product targets Cádiz users and must support Spanish.

Decision:

Use English for code, documentation, API field names, and Git commits. Use English as the i18n source/fallback language
and provide Spanish translations from the beginning.

Consequences:

- All user-facing frontend strings must use the translation system.
- Literal UI strings should not be scattered through React components.

---

### Multi-leg routing is deferred beyond MVP

Context:

The project is conceptually inspired by Rome2Rio, but the initial CTAN-backed application should remain focused and
achievable.

Decision:

MVP supports direct journeys only.

Why:

- Direct service lookup already provides substantial value.
- Proper transfer routing introduces GTFS/routing complexity.
- Keeping routing out of MVP allows focus on data quality and UX.

Consequences:

- No-result messages must say that transfer routes are unsupported rather than claiming no route exists.
- GTFS is investigated early but not used for MVP route planning.

---

### Maps are deferred beyond MVP

Context:

CTAN may expose coordinates and route geometry, but mapping is not required to make direct journey and timetable lookup
useful.

Decision:

Do not let map implementation block MVP.

Consequences:

- Preserve geographic data when available.
- Add map visualization in a later phase.

### 2026-09-06 — Use semantic tokens for the light and dark themes

Context:

The frontend's visual palette is shared across the page shell and place-selection flow. A dark theme should not require
duplicating raw colors throughout React components or maintaining a second frontend styling system.

Decision:

Keep light and dark values in the shared Tailwind theme tokens and override them through a document `data-theme`
attribute. Follow the browser system preference on first visit, then let the header control persist an explicit light or
dark choice in `localStorage`. Bootstrap the document theme before React mounts so the initial page does not flash the
light palette.

Why:

- Keeps component classes semantic and makes future palette adjustments centralized.
- Supports an app-like preference without introducing accounts or a second frontend.
- Preserves the existing web-first architecture and accessibility focus.

Consequences:

- New interface colors must be added as semantic theme tokens rather than raw component-level hex values.
- Both themes need contrast and focus-state checks whenever visual components change.
- PWA remains the preferred next major post-MVP feature; dark mode does not change that ordering.

### 2026-09-06 — Prefer a PWA before a native mobile app

Context:

Gadiruta already has a React + Vite web frontend, and the product should remain web-first while the first-version
journey, schedule, line, stop, alert, localization, and responsive milestones are completed.

Decision:

Make an installable Progressive Web App the highest-priority post-MVP mobile direction. Extend the existing frontend
with a manifest and icons, a service worker and offline app shell, carefully scoped caching for recent transport data,
and predictable update behavior. Do not implement PWA functionality as part of the current MVP.

React Native/Expo remains a later option only if genuinely native requirements emerge that the web platform and PWA
cannot satisfy adequately.

Why:

- Reuses the existing web UI, routing, translations, API boundary, and design system.
- Provides an app-like installation path for Android and iOS without maintaining a second frontend.
- Keeps offline behavior and cached transport data within the established web/API boundaries.
- Defers the cost of native tooling and duplicated platform-specific UI until there is a demonstrated need.

Consequences:

- PWA work is planned immediately after the first-version milestones, before evaluating React Native/Expo.
- Offline data must carry clear freshness semantics and must not be presented as current when stale.
- Service-worker updates need explicit testing and user-facing behavior so old app shells do not persist unexpectedly.
- A native app may still be introduced later if web capabilities prove insufficient.

---

## 2026-09-05 — Cached population-centre catalogue with stable public IDs

Context:

The verified Cádiz catalogue is small (37 centres and 12 municipalities), and the location list
does not document free-text search. The first API slice needs autocomplete without introducing
database synchronization or exposing raw provider identifiers.

Decision:

Fetch and normalize the catalogue on demand, search it locally, and cache it for one hour using
Django's cache API. Start with the default per-process local-memory backend. The TTL is an
application policy, not a verified CTAN refresh interval.

Use UUIDv5 with `uuid.NAMESPACE_URL` and the name
`urn:gadiruta:place:ctan:2:population-centre:{canonical_upstream_id}` for public place IDs. The
canonical upstream ID is its positive decimal representation without leading zeroes. Provider
references initially lived in the internal domain model; the capability-boundary decision below
supersedes that placement without changing the public IDs.

Consequences:

- No new database tables, synchronization jobs, or cache infrastructure for this slice.
- IDs survive cache refreshes, name changes, and record reordering; future persistence must retain
  these public IDs or explicitly migrate consumers. Upstream ID reassignment remains unverified.
- Cache contents are not shared across workers or preserved across process restarts. A production
  caching/synchronization strategy will need review before deployment.
- The first places resource represents population centres only, not physical stops.

The UUIDv5 derivation was superseded before public release by the canonical-identity decision of
2026-09-18.

---

## 2026-09-06 — Capability-specific provider boundary and global attribution

Context:

Place services constructed the CTAN client and assembled its records, while API handlers caught
CTAN exceptions. The internal `Place` also carried consortium and zone fields unused by search.
These dependencies made the application contract unnecessarily specific to its first provider.

Decision:

Use a small `PlaceProvider` protocol returning normalized places and a neutral `ProviderError`.
Select `CTANPlaceProvider` in one explicit wiring module. The CTAN integration owns HTTP clients,
record validation, municipality joins, stable ID derivation, and exception translation. Services
own search, cache policy, and fetch timestamps; API handlers own the public error response.

Keep `Place` limited to the public identity and normalized labels currently needed by the domain.
Provider references remain in integration records, not a speculative generic metadata container.
Add other capability contracts only when implemented; do not introduce a universal provider interface.

Publish data attribution and the independence disclaimer globally in the API overview and existing
web footer. Endpoint descriptions explain behavior without repeating source acknowledgements.

Consequences:

- Existing public UUIDs, response shapes, ranking, one-hour caching, and error behavior are unchanged.
- A provider-neutral, versioned catalogue cache key replaces the CTAN-scoped key and avoids reusing
  snapshots with the old internal domain shape.
- Services and API tests can use a structural provider stub without CTAN metadata or HTTP.
- CTAN errors retain their chained cause inside the integration, but public responses and API logs
  expose no upstream details.
- Multi-provider merging and reverse mapping of public IDs for future capabilities remain separate
  design work; neither is required for today's place catalogue.

---

## 2026-09-18 — Persist canonical place identities and provider crosswalks

Context:

The first place provider derived public UUIDs directly from CTAN population-centre IDs. The
application has not been released and no persisted Gadiruta place IDs exist, so there is no public
identity contract to migrate from that implementation.

Decision:

Persist canonical places and provider-reference crosswalks in PostgreSQL. The first successful
catalogue refresh assigns a fresh UUID4 canonical ID to each previously unmapped provider record.
The active provider refreshes canonical display labels during a successful catalogue cache refresh.
Never infer a crosswalk by matching labels.

Use one environment-selected place provider per deployment, defaulting to CTAN. Do not add runtime
fallback, provider merging, or a universal transport-provider interface. Add a direct-journey
provider contract only when direct journey search is implemented.

Consequences:

- A place's public ID remains stable after its provider-reference crosswalk is first created.
- No compatibility mapping exists for the unreleased CTAN-derived UUIDs.
- Place search now requires PostgreSQL to resolve provider records into canonical identities.
- A later GTFS or commercial-provider adapter can add explicit references to existing canonical
  places; unmatched records remain distinct until a deliberate crosswalk is supplied.
- Full backend tests and pre-push checks require the configured PostgreSQL test database.

---

## 2026-09-18 — Capability-specific CTAN direct journey lookup

Context:

CTAN does not provide a reliable single direct-journey endpoint for a selected date. The
origin/destination endpoint discovers candidate lines but ignores date-like parameters, while the
line timetable endpoint accepts only day and month. It has no reliable year parameter and has
returned working-day tables for observed holidays.

Decision:

Add a separate `DirectJourneyProvider` capability, selected by
`GADIRUTA_DIRECT_JOURNEY_PROVIDER` and implemented initially by CTAN. Resolve public place UUIDs
through that capability's provider-reference crosswalks. CTAN discovers candidate lines, fetches
each dated line timetable with at most four concurrent requests, and extracts only rows whose
unambiguous population-centre groups are in the requested travel order.

Allow dates from today through the end of the current Europe/Madrid calendar year. Cache a complete
normalized result for one hour, then apply the optional departure-time filter locally. Treat
CTAN's exact documented no-data response as a cautious successful empty result. Fail the entire
lookup on any other candidate or timetable failure rather than presenting a partial timetable.

Consequences:

- The public API exposes provider-neutral line code, departure/arrival times, duration, and an
  optional cleaned source note; it does not claim CTAN mode or operator data that the timetable
  rows do not reliably provide.
- The API warns every result that calendar accuracy is not guaranteed, and it does not imply that
  transport is impossible when no direct service is returned.
- A future GTFS, Google Maps, or other provider can implement direct search independently of place
  search, provided explicit canonical-place crosswalks exist for that provider.
- Requests are bounded but a cold search can make several CTAN calls. The one-hour cache avoids
  repeating a complete successful lookup for different departure-time filters.
