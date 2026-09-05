# CTAN API Notes

Primary documentation:

https://api.ctan.es/doc/

Cádiz uses the Bahía de Cádiz consortium (`2`).

This document records **verified discoveries about the upstream CTAN API**.

Do not use it as the reference for Gadiruta's own API.

---

## Discovery checklist

Document the following as the API is explored:

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
6. Missing/null/inconsistent fields.
7. Error responses.
8. Language behavior.
9. Refresh frequency.
10. Useful undocumented or non-obvious behavior.
11. GTFS availability and refresh behavior.
12. Which endpoints are suitable for direct journey search.

---

## Consortium

### Bahía de Cádiz

```text
consortium_id = 2
```

Status: Known from initial project research.

---

## Relevant capabilities identified during initial research

The CTAN portal indicates support for data including:

- Services between population centres.
- Lines.
- Stops.
- Route/line geometry.
- Timetables.
- Operators.
- Alerts/news.
- Fares.
- GTFS data.

These capabilities must still be validated against the actual API responses and parameters before Gadiruta depends on
them.

---

## Direct journey search

Status: To investigate.

Questions to answer:

- Which endpoint returns services between two population centres?
- Does it accept date/time?
- Does it return scheduled departure and arrival times?
- Does it return line/operator identifiers?
- How are directions represented?
- Are results tied to service calendars?
- Can results be filtered to consortium `2`?
- Does it cover all Cádiz-area modes represented by CTAN?
- What happens when no direct service exists?

Record verified request/response examples here once discovered.

---

## Locations / population centres

Status: To investigate.

Questions:

- Endpoint.
- Search/filter parameters.
- Identifier stability.
- Display name fields.
- Municipality relationship.
- Coordinates.
- Language/localized fields.
- Distinction between population centre and physical stop.

---

## Stops

Status: To investigate.

Questions:

- Endpoint.
- Stop identifier.
- Coordinates.
- Lines serving stop.
- Population centre relationship.
- Upcoming departures availability.
- Direction/platform fields.
- Geometry relationship.

---

## Lines

Status: To investigate.

Questions:

- Endpoint.
- Line identifier.
- Public-facing line number/name.
- Operator.
- Direction variants.
- Ordered stops.
- Route geometry.
- Timetable/calendar linkage.
- Active/inactive state.

---

## Timetables and calendars

Status: To investigate.

Questions:

- How weekdays and service calendars are represented.
- Holiday exceptions.
- Date ranges.
- Overnight trips.
- Times past 24:00 if present.
- Seasonal schedules.
- Whether responses are already date-resolved.

---

## Alerts / notices

Status: To investigate.

Questions:

- Endpoint.
- Effective dates.
- Severity.
- Affected line identifiers.
- Affected stop identifiers.
- Free-form HTML/text fields.
- Localization.
- Expiry behavior.

---

## Fares

Status: Future/optional for MVP.

Questions:

- Endpoint.
- Zone/fare model.
- Whether fares can be tied to direct journey results.
- Reliability and completeness for consortium `2`.

---

## GTFS

Status: Investigate during discovery; do not use for MVP routing yet.

Record:

- Feed URL/endpoint.
- Update frequency.
- Included agencies.
- Cádiz coverage.
- `agency.txt`.
- `stops.txt`.
- `routes.txt`.
- `trips.txt`.
- `stop_times.txt`.
- `calendar.txt`.
- `calendar_dates.txt`.
- `shapes.txt`.
- Any feed validation issues.

Future route planning may depend on this feed.

---

## Error handling

Record verified behavior for:

- Invalid parameters.
- Unknown identifiers.
- Empty results.
- Server errors.
- Rate limits if any.
- Timeout behavior.
- Malformed/inconsistent payloads.

Gadiruta must normalize upstream failures into stable application behavior.

---

## Fixtures

Representative API responses should be stored under something similar to:

```text
backend/tests/fixtures/ctan/
```

Normal tests should use fixtures rather than contacting CTAN live.

Capture representative cases for:

- Standard success.
- Empty result.
- Missing optional data.
- Multiple directions.
- Alerts.
- Calendar edge cases.
- Any upstream inconsistency that requires normalization.
