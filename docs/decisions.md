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
canonical upstream ID is its positive decimal representation without leading zeroes. Retain
provider, consortium, and upstream identifiers separately in the internal domain model.

Consequences:

- No new database tables, synchronization jobs, or cache infrastructure for this slice.
- IDs survive cache refreshes, name changes, and record reordering; future persistence must retain
  these public IDs or explicitly migrate consumers. Upstream ID reassignment remains unverified.
- Cache contents are not shared across workers or preserved across process restarts. A production
  caching/synchronization strategy will need review before deployment.
- The first places resource represents population centres only, not physical stops.
