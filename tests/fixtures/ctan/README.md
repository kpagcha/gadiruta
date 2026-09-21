# CTAN response fixtures

Source: [CTAN Open Data API](https://api.ctan.es/doc/), Bahía de Cádiz consortium (`2`).
Catalogue captures: 2026-09-05. Timetable captures: 2026-09-14.
The physical-stop sample was captured on 2026-09-21.
Gadiruta is an independent application, not an official CTAN service.

`metadata.json` records each saved response's request URL, HTTP status, content type, and UTC
retrieval time. JSON is reindented and Unicode escapes decoded for readability; original values
and complete record lists are preserved except where a fixture is explicitly labelled a sample.

| Fixture | Observed response |
| --- | --- |
| `nucleos.json` | 37 population centres; HTTP 200. |
| `municipios.json` | 12 municipalities; HTTP 200. |
| `paradas_sample.json` | First 12 records of the physical-stop catalogue; HTTP 200. |
| `nucleos_empty.json` | Empty centre list for unknown municipality `999999`; HTTP 200. |
| `nucleo_invalid_id.json` | JSON error for centre ID `0`; HTTP 400. |
| `consorcio_not_found.html` | HTML error from the documented consortium-detail path; HTTP 404. |
| `journeys_cadiz_jerez.json`, `journeys_jerez_cadiz.json` | Opposite directions, 45 rows each; HTTP 200. |
| `journeys_cadiz_el_puerto.json` | 106 mixed bus/rail/boat timetable rows, including midnight arrival; HTTP 200. |
| `journeys_cadiz_chiclana.json` | 88 rows with missing passage times and NUL characters in notes; HTTP 200. |
| `journeys_no_data.json` | Valid centres 23 → 49, no-data error; HTTP 400, not a successful empty list. |
| `journeys_missing_origin.json` | Missing parameters, incorrect-origin error; HTTP 400. |
| `frecuencias.json` | 15 frequency entries, including duplicate abbreviations; HTTP 200. |
| `line_13_weekday.json`, `line_13_sunday.json` | Different September 14/20 line tables; HTTP 200. |
| `line_13_october_12.json` | Working-weekday rows despite October 12 being a confirmed 2026 holiday; HTTP 200. |
| `line_158_weekday.json` | C-1: multiple departures and rows without Jerez times. |
| `line_16_weekday.json` | M-050: both directions and a row without Cádiz times. |
| `line_214_weekday.json` | MD: missing intermediate times with usable Cádiz/Jerez times. |
| `line_16_sunday.json` | M-050 September 20 services, one row per direction. |
| `line_13_all_frequencies.json` | Empty date/frequency parameters return both weekday and weekend tables. |
| `line_invalid_date.json` | Invalid day/month return HTTP 400 and a date error. |

`journey_probe_metadata.json` records additional comparisons without duplicating identical bodies.
`calendar_probe_metadata.json` records holiday, year-boundary and explicit-frequency comparisons
against the existing weekday/Sunday fixtures. October 12 and December 25 were checked against
the official 2026 holiday calendar linked in `docs/ctan-api.md`; automatic line-13 requests still
return working-weekday rows. All timetable captures are provider responses, not independent
verification that a service operates on a particular date.
Timetable captures preserve complete records, including escaped control characters and truncated
upstream labels. Dates in filenames describe the request, not independently verified service validity.
These fixtures are discovery evidence for future adapter tests; no journey adapter exists yet.

The empty fixture was not observed on the full consortium catalogue endpoint. Tests deliberately
reuse it there to verify empty-catalogue handling. Tests also reuse error bodies under different
HTTP statuses and inject missing fields, duplicates, malformed payloads, and transport failures.
These are synthetic resilience cases, not additional claims about live upstream behavior.

Normal tests use these files through `httpx.MockTransport`; they never fetch replacement data.
Update captures deliberately, preserve provenance, and document discoveries in
[`docs/ctan-api.md`](../../../docs/ctan-api.md).
