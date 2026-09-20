# Architectural Decisions

This file records durable project decisions and their rationale. Keep entries short; implementation details belong in code or the relevant technical document.

## 1. Keep a separate React frontend and Django API

**Decision:** Gadiruta remains a single repository with a React + TypeScript frontend and Django + Django Ninja backend.

**Why:** The product benefits from rich client-side search interaction and future PWA/map work, while Django remains the server-side domain, persistence, and integration layer.

## 2. Expose a Gadiruta domain, not upstream schemas

**Decision:** Public APIs and frontend code use provider-neutral Gadiruta identities and schemas.

**Why:** CTAN REST, GTFS, Renfe, or other sources may change independently. Provider IDs and payload structures belong behind integration boundaries.

## 3. Use canonical place identities with provider crosswalks

**Decision:** User-facing places have stable Gadiruta identities; provider references are stored separately.

**Why:** Display names can change or collide, and upstream identifiers must not become the application's permanent public identity by accident.

## 4. Keep `Place` above physical transit stops

**Decision:** Population centres remain the search UX. A place may map to multiple physical GTFS stops.

**Why:** Users naturally search for Cádiz, Jerez, San Fernando, etc., while schedule calculation requires actual stop sequences.

## 5. Make GTFS authoritative for static transit data

**Decision:** Migrate routes, stops, trips, stop times, calendars, exceptions, shapes, agencies, and direct-journey lookup from CTAN REST to imported GTFS data.

**Why:** GTFS models schedules and full calendar dates explicitly, supports local queries, avoids CTAN REST's ambiguous timetable/calendar behavior, and is the appropriate foundation for later routing.

**Consequence:** Existing REST direct-journey code is transitional and should be retired after GTFS parity/coverage is verified.

## 6. Retain CTAN REST only for justified gaps

**Decision:** CTAN REST may remain for capabilities GTFS does not provide, such as population-centre metadata, alerts, or supplementary provider-specific data.

**Why:** Keeping REST integrations by inertia adds provider coupling without product value.

## 7. Import GTFS locally and activate datasets atomically

**Decision:** Download/import GTFS on a schedule, validate a candidate dataset, and only then make it active. A failed refresh must leave the previous valid dataset available.

**Why:** Journey search should not depend on live CTAN availability or expose partially imported data.

**Initial implementation:** Django management command plus cron/scheduler. Celery/Redis are not required solely for imports.

## 8. Direct journeys first; no custom transfer router

**Decision:** MVP journey lookup matches direct trips only. Multi-leg routing is deferred.

**Why:** Direct services deliver useful product value without the complexity of transfer routing.

**Future:** Use a mature GTFS routing engine such as OpenTripPlanner rather than implementing a general-purpose routing algorithm in Gadiruta.

## 9. PostgreSQL is the durable backend store

**Decision:** PostgreSQL stores canonical identities and is the intended store for imported/normalized transit data.

**Why:** The project needs durable crosswalks, import metadata, relational GTFS data, and efficient local journey queries.

## 10. Keep the product web-first

**Decision:** Extend the current React/Vite application into a PWA after the MVP rather than building a parallel native app now.

**Why:** One frontend keeps product and engineering scope smaller while still supporting installability and offline shell behavior. React Native/Expo should be reconsidered only for requirements the web platform cannot meet well.
