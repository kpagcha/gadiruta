# CTAN response fixtures

Source: [CTAN Open Data API](https://api.ctan.es/doc/), Bahía de Cádiz consortium (`2`).
Captured on 2026-09-05. Gadiruta is an independent application, not an official CTAN service.

`metadata.json` records each saved response's request URL, HTTP status, content type, and UTC
retrieval time. JSON is reindented and Unicode escapes decoded for readability; original values
and complete record lists are preserved.

| Fixture | Observed response |
| --- | --- |
| `nucleos.json` | 37 population centres; HTTP 200. |
| `municipios.json` | 12 municipalities; HTTP 200. |
| `nucleos_empty.json` | Empty centre list for unknown municipality `999999`; HTTP 200. |
| `nucleo_invalid_id.json` | JSON error for centre ID `0`; HTTP 400. |
| `consorcio_not_found.html` | HTML error from the documented consortium-detail path; HTTP 404. |

The empty fixture was not observed on the full consortium catalogue endpoint. Tests deliberately
reuse it there to verify empty-catalogue handling. Tests also reuse error bodies under different
HTTP statuses and inject missing fields, duplicates, malformed payloads, and transport failures.
These are synthetic resilience cases, not additional claims about live upstream behavior.

Normal tests use these files through `httpx.MockTransport`; they never fetch replacement data.
Update captures deliberately, preserve provenance, and document discoveries in
[`docs/ctan-api.md`](../../../docs/ctan-api.md).
