"""Translate verified CTAN records into provider-scoped places and direct services."""

import re
import unicodedata
from datetime import time

from transport.domain import DirectJourney, ProviderPlace
from transport.integrations.ctan.schemas import (
    CandidateLine,
    Municipality,
    PopulationCentre,
    TimetablePlaceGroup,
    TimetablePlanner,
    TimetableRow,
)


def to_places(
    centres: list[PopulationCentre], municipalities: list[Municipality]
) -> tuple[ProviderPlace, ...]:
    """Join municipality names while keeping CTAN references inside the provider boundary.

    Missing municipality relationships yield an unknown label rather than dropping a usable centre.
    Canonical public identity is resolved by the application after this adapter returns.
    """
    names = {municipality.upstream_id: municipality.name for municipality in municipalities}
    return tuple(
        ProviderPlace(
            external_id=centre.upstream_id,
            name=centre.name,
            municipality=names.get(centre.municipality_id) if centre.municipality_id else None,
        )
        for centre in centres
    )


def to_direct_journeys(
    origin: ProviderPlace,
    destination: ProviderPlace,
    candidates: list[CandidateLine],
    planners_by_line: dict[str, list[TimetablePlanner]],
) -> tuple[DirectJourney, ...]:
    """Extract usable direct services from dated CTAN line tables in deterministic order.

    CTAN line planners identify population-centre groups by labels rather than IDs. A direction is
    used only when origin and destination labels each occur exactly once and origin precedes
    destination. This intentionally skips ambiguous data rather than inventing a stop mapping.
    """
    journeys: list[DirectJourney] = []
    for candidate in candidates:
        for planner in planners_by_line[candidate.upstream_id]:
            journeys.extend(
                _extract_direction(
                    origin.name,
                    destination.name,
                    candidate.code,
                    planner.outbound_groups,
                    planner.outbound_rows,
                )
            )
            journeys.extend(
                _extract_direction(
                    origin.name,
                    destination.name,
                    candidate.code,
                    planner.inbound_groups,
                    planner.inbound_rows,
                )
            )
    return tuple(
        sorted(
            journeys,
            key=lambda journey: (
                journey.departure_time,
                journey.arrival_time,
                journey.line_code,
                journey.note or "",
            ),
        )
    )


def _extract_direction(
    origin_name: str,
    destination_name: str,
    line_code: str,
    groups: list[TimetablePlaceGroup],
    rows: list[TimetableRow],
) -> list[DirectJourney]:
    """Extract rows from one planner direction when its place groups match the request safely."""
    if not groups:
        return []
    origin_index = _unique_group_index(groups, origin_name)
    destination_index = _unique_group_index(groups, destination_name)
    if origin_index is None or destination_index is None or origin_index >= destination_index:
        return []
    ranges = _group_ranges(groups)
    origin_range = ranges[origin_index]
    destination_range = ranges[destination_index]
    journeys: list[DirectJourney] = []
    for row in rows:
        if len(row.times) != ranges[-1].stop:
            continue
        departure_times = _valid_times(row.times[origin_range.start : origin_range.stop])
        arrival_times = _valid_times(row.times[destination_range.start : destination_range.stop])
        if not departure_times or not arrival_times:
            continue
        departure = min(departure_times)
        arrival = max(arrival_times)
        duration_minutes = (arrival.hour * 60 + arrival.minute) - (
            departure.hour * 60 + departure.minute
        )
        if duration_minutes < 0:
            duration_minutes += 24 * 60
        journeys.append(
            DirectJourney(
                line_code=line_code,
                departure_time=departure,
                arrival_time=arrival,
                duration_minutes=duration_minutes,
                note=_clean_note(row.note),
            )
        )
    return journeys


def _unique_group_index(groups: list[TimetablePlaceGroup], name: str) -> int | None:
    """Return one accent-insensitive exact group match or None when matching is ambiguous."""
    normalized_name = _fold_text(name)
    matches = [
        index for index, group in enumerate(groups) if _fold_text(group.name) == normalized_name
    ]
    return matches[0] if len(matches) == 1 else None


def _group_ranges(groups: list[TimetablePlaceGroup]) -> list[range]:
    """Convert CTAN column spans into zero-based ranges that partition one timetable row."""
    start = 0
    ranges: list[range] = []
    for group in groups:
        stop = start + group.colspan
        ranges.append(range(start, stop))
        start = stop
    return ranges


def _valid_times(values: list[str]) -> list[time]:
    """Parse supplied CTAN times while leaving its missing marker out of journey calculations."""
    return [time.fromisoformat(value) for value in values if value != "--"]


def _clean_note(note: str | None) -> str | None:
    """Remove CTAN controls and collapse display whitespace without translating its content."""
    if note is None:
        return None
    cleaned = re.sub(
        r"\s+", " ", "".join(character if character.isprintable() else " " for character in note)
    )
    return cleaned.strip() or None


def _fold_text(value: str) -> str:
    """Compare provider labels without case, accent, or whitespace variation."""
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(
            character for character in normalized if not unicodedata.combining(character)
        ).split()
    )
