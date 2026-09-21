# GTFS test feed

`minimal/` is a small valid GTFS feed used to assemble deterministic ZIP archives in tests. It has
one agency, one bus route, one trip, three stops, a normal weekly calendar, a calendar exception,
and a route shape. It is synthetic and must not be treated as CTAN data.

Normal tests never download CTAN's feed. The `inspect_gtfs` management command can inspect a local
archive during development or the published CTAN archive only when explicitly run.
