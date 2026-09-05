# CTAN API Notes

Primary documentation:

[CTAN API documentation](https://api.ctan.es/doc/). Its generated definitions are in
[`api_data.js`](https://api.ctan.es/doc/api_data.js) and
[`api_project.js`](https://api.ctan.es/doc/api_project.js).

The documentation metadata reports version `1.0.0`, generated on 2020-02-14, and an HTTP base URL.
Live discovery on 2026-09-05 verified HTTPS at `https://api.ctan.es/v1`; Gadiruta uses HTTPS.
Documented examples are not sufficient evidence of current response behavior.

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

Status: Location and municipality lists for consortium `2` verified live on 2026-09-05.

The documented `/Consorcios/2/consorcio` detail URL returned HTTP 404 with an HTML body. The
place-search integration does not depend on that resource.

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

Status: Documentation inspected; live behavior and calendar semantics still unverified.

The documented candidate is `/Consorcios/:idConsorcio/horarios_origen_destino`, described as
services between population centres, not arbitrary street addresses or physical stops. Its example
uses `origen=1&destino=46&lang=ES`, while its parameter table calls the IDs `idNucleoOrigen` and
`idNucleoDestino`. No date parameter appears in that table. Exercise real requests and save
fixtures before choosing parameters, interpreting calendars, or implementing direct services.

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

No live journey response has been captured yet.

---

## Locations / population centres

Status: Catalogue and municipality relationship verified live on 2026-09-05.

Paths below are relative to `https://api.ctan.es/v1/Consorcios/2/`.

| GET path | Observed body | Records |
| --- | --- | --- |
| `nucleos` | Object with a `nucleos` array | 37 |
| `municipios/` | Object with a `municipios` array | 12 |
| `municipios/6/nucleos` | Object with a `nucleos` array | 10 |
| `municipios/999999/nucleos` | `{"nucleos": []}` | 0 |

All four returned HTTP 200 and JSON. No search text or pagination parameters are documented for
these lists. The implementation fetches the small catalogue and searches it locally.

Population-centre fields observed:

- `idNucleo`: positive numeric identifier represented as a string.
- `nombre`: display name, including accented names such as `Cádiz`.
- `idMunicipio`: municipality identifier, also a numeric string.
- `idZona`: letter-valued zone, such as `A` or `K`, not a numeric identifier.

Municipality records use `idMunicipio` for the ID and `datos` for the display name. All municipality
references in the captured centre list resolve against the municipality list. Centre `1` is Cádiz
in municipality `1`; centre `42` is Aeropuerto in municipality `6` (Jerez de la Frontera), zone `K`.
The centre named `Jerez` is not labelled identically to its municipality. Display spelling can
also differ: `Sanlúcar de Barrameda` in the centre list, `Sanlucar de Barrameda` in municipalities.

The catalogue includes centres sharing part of a name, such as Costa Ballena entries in different
municipalities. Names must not define identity. CTAN documents population centres (`nucleos`) and
physical stops (`paradas`) as separate resources; this capture does not establish physical-stop
relationships.

No coordinates or translated-name fields were present in these lists. Requests for
`nucleos?lang=EN` and `nucleos?lang=ES` returned identical bodies to the unqualified list; language
support for other endpoints is not established by this observation. Preserve provider names.

Still unverified: identifier stability across upstream changes, refresh frequency, physical-stop
relationships, and alternative sources of centre coordinates. Missing fields and inconsistent
records in the resilience tests are synthetic; they were not observed in this success capture.

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

Observed on 2026-09-05:

- `/Consorcios/2/nucleos/0` returned HTTP 400 with a JSON `error` stating that the identifier must
  be greater than zero. The documentation's error example uses 404 instead.
- `/Consorcios/2/municipios/999999/nucleos` returned HTTP 200 with an empty list, not an error.
- `/Consorcios/2/consorcio` returned HTTP 404 with HTML rather than JSON.

These statuses are endpoint-specific observations, not a universal CTAN error contract. Live
rate limits, server failures, timeouts, and malformed catalogue responses remain unverified.
Automated tests simulate them behind the HTTP adapter.

Continue investigating:

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

Representative captured response bodies and request metadata are stored under:

```text
tests/fixtures/ctan/
```

See the fixture README and `metadata.json` for exact request URLs, retrieval times, statuses, and
the distinction between observed responses and synthetic test cases. Normal tests use fixtures
rather than contacting CTAN live.

Capture representative cases for:

- Standard success.
- Empty result.
- Missing optional data.
- Multiple directions.
- Alerts.
- Calendar edge cases.
- Any upstream inconsistency that requires normalization.
