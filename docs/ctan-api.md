# CTAN Data Notes

This document records verified or strategically relevant facts about CTAN upstream data. It is **not** the reference for Gadiruta's own API; use generated OpenAPI for that.

Primary CTAN REST documentation: https://api.ctan.es/doc/

Cádiz uses the Bahía de Cádiz consortium ID `2`.

## Direction

CTAN REST was initially used for place search and direct timetable lookup. The project is now moving static network/schedule data to CTAN's GTFS feed because GTFS provides a standard, date-aware model for routes, trips, stop times, service calendars, calendar exceptions, and shapes.

After migration, REST should remain only for capabilities GTFS does not provide adequately.

## Population centres and municipalities

Verified for consortium `2`:

| Path relative to `/v1/Consorcios/2/` | Purpose |
| --- | --- |
| `nucleos` | Population-centre catalogue. |
| `municipios/` | Municipality catalogue. |
| `municipios/{id}/nucleos` | Population centres for a municipality. |

Observed population-centre fields include:

- `idNucleo`;
- `nombre`;
- `idMunicipio`;
- `idZona`.

Municipality records use `idMunicipio` and `datos` for the label.

Important observations:

- names are presentation data and are not safe identities;
- `núcleos` and physical stops (`paradas`) are separate CTAN concepts;
- the `núcleos` responses observed do not contain coordinates;
- EN/ES requests returned the same place labels in the captured catalogue;
- unknown municipality IDs may return HTTP 200 with an empty `nucleos` array.

Gadiruta currently uses this small catalogue for user-facing `Place` search and persists canonical identities/provider crosswalks.

## REST timetable findings

### `horarios_origen_destino`

Example:

```text
GET /v1/Consorcios/2/horarios_origen_destino?origen=1&destino=8&lang=ES
```

The endpoint returns timetable rows/services between population centres, including line IDs/codes, stop-zone columns, times, frequency labels, and observations.

It does **not** accept a concrete date. It returns service-pattern rows such as `L-V`, `S-D-F`, or `L-D` rather than resolving a requested calendar date.

### `horarios_lineas`

Example shape:

```text
GET /v1/Consorcios/2/horarios_lineas?linea=158&dia=18&mes=9&frecuencia=&lang=ES
```

Observed behavior for line `158`:

- blank `frecuencia` filters rows according to the supplied day/month's ordinary weekday/weekend category;
- explicit `frecuencia` selects that frequency category directly;
- the response exposes frequency metadata such as `L-V`, `S-D-F`, and `L-D`;
- the request has day/month but no reliable year parameter.

For the tested C-1 data, frequency IDs included:

- `1`: `L-V` — lunes a viernes laborables;
- `2`: `S-D-F` — sábados, domingos y festivos;
- `7`: `L-D` — diario, incluido festivos.

Do **not** assume those numeric IDs are globally stable across all CTAN lines/consortia unless verified.

### Why REST is not the long-term schedule source

The REST timetable model creates avoidable ambiguity:

- direct origin/destination lookup is not date-specific;
- line lookup uses day/month without a robust year dimension;
- holiday treatment is not sufficiently explicit/reliable for future-date journey planning;
- no REST endpoint has been identified that publishes the concrete holiday/service-date calendar used by schedules.

The existing REST direct-journey implementation is transitional and should be retired after GTFS parity is established.

## GTFS

CTAN publishes a unified GTFS feed at:

```text
https://api.ctan.es/v1/datos/UNIFICADO/gtfs.zip
```

The feed contains the standard files needed by Gadiruta's static transit model:

- `agency.txt`;
- `stops.txt`;
- `routes.txt`;
- `trips.txt`;
- `stop_times.txt`;
- `calendar.txt`;
- `calendar_dates.txt`;
- `shapes.txt`.

The archive inspected on 21 September 2026 was a valid ZIP with those eight root-level files.
Its `agency.txt` has non-standard leading whitespace before `agency_name`; GTFS readers should
trim header-field whitespace while still rejecting duplicate or missing normalized names.
`stops.txt` also contains unescaped double quotes inside some quoted stop names. A tolerant CSV
reader preserves the observed field boundaries; validate parsed headers and row completeness rather
than rejecting the whole otherwise usable archive for that upstream formatting defect.

A real import of that archive also found that `shape_pt_sequence` can be zero-based, so ordered shape
sequences must accept zero. Some `trips.txt` rows (for example `6_116_V`) reference a `shape_id` not
present in `shapes.txt`. Preserve the supplied identifier, but treat geometry as unavailable for
those trips rather than rejecting their valid timetable data.

This feed should become authoritative for static transit-network and schedule data.

### Verified unified-feed coverage

The 21 September 2026 inspection reported:

- 9 agencies, including Bahía de Cádiz;
- 5,013 stops, 484 routes, 14,824 trips, and 296,863 stop times;
- GTFS route type `3` (bus) on 482 routes and type `4` (ferry) on 2 routes;
- service-calendar records and exceptions spanning 2017-01-01 through 2038-04-30.

The unified archive has no rail or Trambahía route type in that snapshot. Gadiruta needs another
authoritative source for those modes if they remain part of the Cádiz MVP coverage.

### Important GTFS advantages

- full service dates and validity ranges rather than ambiguous day/month lookups;
- explicit calendar exceptions through `calendar_dates.txt`;
- stop-by-stop trip times;
- standard route/trip/agency relationships;
- route shapes;
- a direct path toward later use with a mature routing engine.

### Known GTFS limitation for Gadiruta places

The current `stops.txt` observed for CTAN contains physical stop identity/name/coordinates but no municipality or `núcleo` field.

GTFS alone therefore does not replace the user-facing place hierarchy. CTAN's documented
`/Consorcios/2/paradas` catalogue does provide `idParada`, `idNucleo`, and physical-stop metadata.
The 21 September 2026 capture verified that matching Bahía de Cádiz GTFS IDs use `2_<idParada>`;
sampled matching records had the same names and coordinates. Gadiruta's `link_ctan_gtfs_places`
command uses that exact ID relationship and never matches on labels.

The live catalogue refresh on that date created 152 active-feed links covering 25 population centres.
Some CTAN physical stops are absent from the unified GTFS snapshot, so no link is created unless the
exact source ID is present in the active feed. Refresh the crosswalk after each GTFS import.

For later supplementary feeds or providers, preferred association sources remain:

1. an authoritative stop-to-place relationship;
2. a deterministic source-ID crosswalk verified against coordinates and coverage;
3. locally persisted place geometry/locality data and spatial association.

Do not infer associations from display names alone.

### ID relationships

The stop relation `2_<idParada>` is now verified for the current Bahía de Cádiz snapshot and is used
only by the managed crosswalk refresh. Other apparent patterns, such as route IDs shaped like `2_13`,
remain useful clues rather than contracts until their stability and coverage are verified.

### Remaining coverage work

The unified archive is sufficient to begin local bus/ferry import and direct-journey work. Before
retiring the current REST timetable path, establish the place-to-stop crosswalk and identify an
authoritative feed for rail/Trambahía if those modes remain in scope. Add supplementary feeds behind
the same normalized domain rather than reintroducing CTAN-specific journey logic.

## Alerts and other remaining REST capabilities

Still investigate:

- service alerts/notices and their affected lines/stops;
- whether CTAN offers GTFS-Realtime or another structured alert source;
- fares if they become a product priority;
- any supplementary provider metadata that GTFS genuinely lacks.

Each retained REST dependency should have an explicit reason.

## Error behavior

Observed REST behavior is endpoint-specific rather than uniform. Examples include:

- invalid `nucleo` ID returning JSON HTTP 400;
- unknown municipality returning HTTP 200 with an empty result;
- a documented consortium-detail URL returning HTML HTTP 404.

Normalize upstream failures at the integration boundary. Do not expose CTAN error shapes directly to API consumers.

## Fixtures and discovery

Representative CTAN REST fixtures live under `tests/fixtures/ctan/` and should remain the basis of deterministic REST adapter tests.

For GTFS, add compact representative test feeds covering:

- normal weekday service;
- weekend/holiday exceptions;
- additions/removals in `calendar_dates.txt`;
- multiple stops per place;
- origin-before-destination matching;
- overnight times;
- invalid/incomplete feed rejection;
- atomic activation/fallback to the previous valid dataset.

Record new upstream discoveries here only when they affect design, parsing, reliability, or retained provider dependencies.
