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

Status: Candidate-line lookup followed by dated line timetables verified for Cádiz ↔ Jerez
on 2026-09-14. Automatic holiday handling and explicit year selection are not reliable.

The documented candidate is `/Consorcios/:idConsorcio/horarios_origen_destino`, described as
services between population centres, not arbitrary street addresses or physical stops. Its example
uses `origen=1&destino=46&lang=ES`, while its parameter table calls the IDs `idNucleoOrigen` and
`idNucleoDestino`. No date parameter appears in that table. The observations below resolve
parameter naming, but leave calendar interpretation open.

Discovery questions (partially answered below):

- Which endpoint returns services between two population centres?
- Does it accept date/time?
- Does it return scheduled departure and arrival times?
- Does it return line/operator identifiers?
- How are directions represented?
- Are results tied to service calendars?
- Can results be filtered to consortium `2`?
- Does it cover all Cádiz-area modes represented by CTAN?
- What happens when no direct service exists?

### Verified response behavior (2026-09-14)

Both `origen`/`destino` and `idNucleoOrigen`/`idNucleoDestino` accepted population-centre
IDs. The alternate names returned the same parsed Jerez-to-Cádiz response as the example
names. Prefer `origen`/`destino`, matching CTAN's example; mixed-name precedence was not tested.

| Origin → destination | IDs | HTTP status | Timetable rows |
| --- | --- | --- | --- |
| Cádiz → Jerez | 1 → 14 | 200 | 45 |
| Jerez → Cádiz | 14 → 1 | 200 | 45 |
| Cádiz → El Puerto de Santa María | 1 → 8 | 200 | 106 |
| El Puerto de Santa María → Cádiz | 8 → 1 | 200 | 105 |
| Cádiz → Chiclana | 1 → 3 | 200 | 88 |
| Torrecera → Costa Ballena (Chipiona) | 23 → 49 | 400 | `No se encuentran los datos` |

Missing origin and origin `0` returned HTTP 400 with an incorrect-origin error. Unknown
destination `999999` returned the same 400/body as the sparse valid pair above. No successful
empty-array response was observed: this error alone does not prove there is no direct service.

The successful body is a table: `bloques`, `horario`, `frecuencias`, `nucleos`, and
`observacionesModoTransporte`. Each row has `idlinea`, `codigo`, an array of `horas`, `dias`,
`observaciones`, and an undocumented `demandahoras` string. It has no explicit operator,
per-row transport mode, service date, validity interval, or direction ID. Request direction
changes the table; do not reverse an existing response locally.

In the captures, `horas` aligns with the passage columns in `bloques`, excluding the leading
line column and trailing frequency/notes columns. `nucleos` groups those columns with numeric
`colspan` values, including a leading blank line-column group. Cádiz → Jerez has four Cádiz
and five Jerez passage columns. These labels can describe grouped stops/zones and have no
physical-stop IDs; preserve their meaning rather than inventing precise stop identities.
`tipo` is not a reliable passage-column discriminator here: all captured OD headers use `1`.

`--` means no time is supplied at that column; it must not become midnight. Different services
use different columns. Cádiz → El Puerto includes a B-042 row from `23:30` to `00:00`, so
clock ordering alone cannot determine duration without overnight handling. No times above
23:59 were observed. Bus notes warn that intermediate passage times depend on traffic.
Bus, boat and rail codes occur, but mode coverage/completeness was not established.

Notes include literal NUL characters after JSON decoding, truncated text and embedded newlines.
Keep the original fixture values; a future adapter must clean display text. Treat `demandahoras`
as opaque: its apparent line/service/frequency encoding is undocumented and not a stable contract.

### Line transport modes (2026-09-18)

The documented `lineas?lang=ES` endpoint works for consortium `2` and returns a catalogue of
`idLinea` records with `codigo`, `modo`, `idModo`, and operator text. Representative live records
include B-042 (`BARCO`), C-1 (`CERCANÍAS`), MD (`MEDIA DISTANCIA`), and M-050 (`AUTOBUS`). The
smaller `lineas/{idLinea}?lang=ES` detail endpoint also works: line `16` returns `M-050` with
`modo="AUTOBUS"`, but includes extensive geometry that direct search does not need.

Use the line catalogue as an ID-to-mode map after origin/destination candidate discovery. It safely
associates each candidate line with a mode, unlike `observacionesModoTransporte`, whose modes are
only listed at the aggregate origin/destination response level. The mode list is presentation
metadata, not timetable data: cache it separately for one hour and treat an unavailable, absent, or
unrecognized value as `unknown` without failing a usable direct-journey response.

### Implemented composition

Use `horarios_origen_destino` to discover distinct candidate line IDs, then request
`horarios_lineas?linea={id}&frecuencia=&dia={day}&mes={month}&lang=ES` for each. Extract every
usable service for the requested direction and combine departures across lines; the pair does
not identify a single line or departure. There is no need to join individual OD and line rows
by the opaque `demandahoras` field. The dated line table supplies the service rows.

Gadiruta implements this composition behind its direct-journey provider capability. It accepts the
exact `400 {"error": "No se encuentran los datos"}` response as a successful empty result, but
the UI must phrase that cautiously because the same response also occurs for an unknown destination.
Any other candidate or dated-timetable failure fails the complete lookup; no partial candidate-line
list is displayed. Do not silently force every holiday to one frequency ID: frequency sets differ
between lines. The date policy remains limited to the current calendar year and warns callers that
calendar accuracy is not guaranteed.

### Candidate-line follow-up (2026-09-14)

The saved Cádiz ↔ Jerez OD tables identify the same eight candidate lines. All eight line
requests succeeded for September 14 with one planner and both direction tables:

| Line ID / code | Usable Cádiz → Jerez rows | Usable Jerez → Cádiz rows |
| --- | --- | --- |
| 214 / MD | 12 | 12 |
| 158 / C-1 | 23 | 23 |
| 177 / M-053 | 1 | 1 |
| 36 / M-902 | 1 | 1 |
| 18 / M-052 | 1 | 1 |
| 38 / M-904 | 1 | 1 |
| 16 / M-050 | 1 | 1 |
| 17 / M-051 | 1 | 1 |
| Total | 41 | 41 |

These are timetable-row counts, not a guarantee of complete real-world transport coverage.
Only the three representative weekday responses (C-1, M-050 and MD) are retained as fixtures;
the other five were inspected during discovery and their observed counts are recorded above.
Select direction by the order of the requested population-centre groups, not by assuming
`Ida` always means outbound from the user's origin. In this sample `Ida` contains Cádiz before
Jerez and `Vuelta` the reverse. Group names match the saved population-centre labels, but no
centre IDs are included; missing or ambiguous name matches must not be guessed.

For each direction, cumulative `nucleosIda`/`nucleosVuelta.colspan` values delimit each centre's
passage columns. Their sum matched each row's `horas` length in all eight inspected responses. Passage
headers are `tipo="0"`; trailing metadata headers vary (C-1 has no observations header), so
do not remove a fixed number of trailing headers. Repeated labels such as `Estación FC` belong
to different centre groups: never match stop labels globally without their group context.

A usable row has at least one supplied time in both requested groups, in travel order. Preserve
all supplied boarding/alighting labels within those groups; do not multiply one service into
separate journey results for every column combination. Missing times in unrelated groups do
not invalidate a journey, and `--` alone does not explain why a time is absent.

Concrete missing-time cases:

- M-050 `Vuelta` has an airport/Jerez row `16:15,16:35,16:45,--,--,--,--,--`; all Cádiz
  columns are absent, so it cannot supply a Jerez → Cádiz result. Its `07:00` Jerez departure
  does have Cádiz times (`07:33` through `07:45`) and remains usable.
- C-1 has 27 rows per direction, but four in each lack all Jerez times. For example, the
  `07:15` Cádiz row supplies times only through San Fernando. Excluding those leaves 23.
- MD's `08:40` Cádiz row lacks Puerto Real and airport times but supplies Jerez `09:13`:
  it remains usable for Cádiz → Jerez.

The Sunday M-050 request returns one row per direction, confirming that the same candidate
line can contribute different dated services. This discovery verifies one pair across eight
lines; catalogue-wide name consistency, future seasonal candidate coverage, multiple planners
and duplicate-service handling remain implementation considerations, not proven API guarantees.

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

Status: Frequency catalogue and one line's date behavior inspected live on 2026-09-14.

`frecuencias?lang=ES` returned 15 entries using `idFreq`, `codigo`, `nombre`, whereas the OD
legend uses `idfrecuencia`, `acronimo`, `nombre`. IDs are consortium-specific. Codes are not
unique: IDs `1` and `9` both use `L-V`, for working weekdays and Monday–Friday respectively.
There are also isolated-day and shopping-holiday descriptions, without actual calendar dates.
The generated API definitions expose no dedicated holiday/calendar endpoint.

Adding `dia=20&mes=9&fecha=2026-09-20` to Cádiz → El Puerto produced the same complete parsed
response as the undated request, including mixed weekday/weekend rows. These guessed date
parameters did not establish date filtering; this does not rule out other undocumented inputs.

The documented line endpoint is `horarios_lineas`; its example uses `linea` and `frecuencia`
although its parameter table calls them `idLinea` and `idFrecuencia`. With
`linea=13&frecuencia=&lang=ES`, live requests produced:

| Date parameters | Outbound / inbound rows | Outbound frequency |
| --- | --- | --- |
| `dia=14&mes=9` | 8 / 3 | `L-V` |
| `dia=20&mes=9` | 4 / 4 | `S-D-F` |
| `dia=12&mes=10` | 8 / 3 | `L-V` |

The first two results agree with Monday/Sunday in 2026 and show actual row filtering. Adding
the undocumented `year=2025` to September 14 returned the same parsed weekday response.

The response contains `planificadores` with `fechaInicio`, `fechaFin`, `especial`, separate
`bloquesIda`/`bloquesVuelta`, `nucleosIda`/`nucleosVuelta`, and `horarioIda`/`horarioVuelta`.
The captured planner starts `2024-06-20`, has an empty end date and `especial="0"`. Unlike OD
headers, passage blocks use `tipo="0"`. `horaCorte` is `1900-01-01 04:00:00.000`; its service-day
meaning remains unverified. Blank row `demandahoras` values provide no proven cross-endpoint
service identity. Seasonal changes, holiday exceptions and overnight service-day assignment
remain unresolved; one line's behavior is not a consortium-wide calendar contract.

### Published timetable sanity check (2026-09-14)

The [official M-040 passenger timetable](https://siu.cmtbc.es/es/horarios_lineas_tabla.php?linea=13)
agrees with the saved line-13 weekday and Sunday tables: eight/three working-weekday rows and
four/four weekend/holiday rows in the two directions. Spot-checked passage times also match,
including outbound 06:30 → 07:13 on weekdays and 10:30 → 11:14 on weekends/holidays.
Its legend explicitly assigns `S-D-F` to Saturdays, Sundays and holidays, supporting the
diagnosis that automatic holiday group selection is the problem in this sample. The same
legend describes absent passage times as no stop in that zone.

This is consistency with the consortium's public presentation, not independent operator-data
validation. The [operator-hosted PDF found in the check](https://www.tgcomes.es/wp-content/uploads/2023/09/CADIZ-EL-PUERTO-SANTA-MARIA.pdf)
is a September 2023 regatta special timetable and was rejected as current evidence. No further
fixtures were added for this limited sanity check; it does not establish network-wide accuracy.

### Calendar follow-up (2026-09-14)

Further line-13 requests establish the limits of automatic date filtering:

| Parameters (with empty `frecuencia` unless specified) | Observed result |
| --- | --- |
| `dia=12&mes=10` | Same working-weekday table as September 14. |
| `dia=25&mes=12` | Same working-weekday table as September 14. |
| `dia=31&mes=12` | Same working-weekday table as September 14. |
| `dia=4&mes=1` | Same weekend table as September 20. |
| `dia=4&mes=1&year=2027&anio=2027&ano=2027` | Unchanged weekend table. |
| `dia=20&mes=9&frecuencia=1` | Working-weekday table despite the Sunday date. |
| `dia=12&mes=10&frecuencia=2` | Weekend/holiday table instead of the automatic weekday table. |
| `dia=&mes=&frecuencia=` | Both frequency groups, 12 outbound and 7 inbound rows. |
| `dia=32&mes=13` | HTTP 400, `La fecha es incorrecta`. |

October 12 and December 25 are confirmed 2026 holidays in the
[official Andalusian calendar](https://www.juntadeandalucia.es/boja/2025/93/1).
CTAN nevertheless selected `L-V` (working weekdays) for this line on both dates. This is
evidence that automatic holiday selection cannot be relied on here; it does not establish
the actual operator's holiday departures. Explicit `frecuencia` takes precedence in the tested
conflicts and selects a schedule group, not an independently validated service calendar.

January 4 is Sunday in 2026 and Monday in 2027. The weekend result supports the inference that
day/month refer to the current calendar year, rather than the next occurrence after the request.
The tested year aliases do not enable 2027 selection. December 31 → January 4 therefore cannot
be treated as a verified 2026 → 2027 search window. This is an observed limitation, not proof
that all possible undocumented year parameters are ignored. A current-year restriction alone
would still leave the demonstrated holiday problem unresolved.

Additional January 3 probes (with separate `anio=2027` and `ano=2027`) also returned the weekend
table, but do not distinguish years because January 3 is a weekend in both 2026 and 2027.
Exact requests and equivalent-body comparisons are retained in `calendar_probe_metadata.json`.

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
