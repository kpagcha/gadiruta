"""Validated CTAN records; upstream aliases stay inside the integration."""

import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, StringConstraints


def normalize_identifier(value: object) -> str:
    """Canonicalize a positive integer or decimal string, raising ValueError otherwise."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Expected a positive CTAN identifier.")
    text = str(value).strip()
    if not re.fullmatch(r"[0-9]+", text) or int(text) <= 0:
        raise ValueError("Expected a positive CTAN identifier.")
    return str(int(text))


def optional_identifier(value: object) -> str | None:
    """Normalize an optional provider reference, discarding missing or invalid values."""
    try:
        return normalize_identifier(value)
    except ValueError:
        return None


def optional_text(value: object) -> str | None:
    """Trim optional text and map blank or non-string values to None."""
    if not isinstance(value, str):
        return None
    return value.strip() or None


Identifier = Annotated[str, BeforeValidator(normalize_identifier)]
OptionalIdentifier = Annotated[str | None, BeforeValidator(optional_identifier)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class CTANRecord(BaseModel):
    """Provide a canonical identifier for validating and deduplicating provider records."""

    upstream_id: Identifier


class PopulationCentre(CTANRecord):
    """Validate a CTAN centre while tolerating absent municipality and zone references."""

    upstream_id: Identifier = Field(alias="idNucleo")
    municipality_id: OptionalIdentifier = Field(default=None, alias="idMunicipio")
    name: Label = Field(alias="nombre")
    zone: Annotated[str | None, BeforeValidator(optional_text)] = Field(
        default=None, alias="idZona"
    )


class Municipality(CTANRecord):
    """Map CTAN's municipality identifier and datos label to named provider fields."""

    upstream_id: Identifier = Field(alias="idMunicipio")
    name: Label = Field(alias="datos")


def normalize_passage_time(value: object) -> str:
    """Accept CTAN's missing marker or a strict 24-hour timetable time."""
    if not isinstance(value, str):
        raise ValueError("Expected a timetable time.")
    text = value.strip()
    if text == "--" or re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", text):
        return text
    raise ValueError("Expected a timetable time.")


PassageTime = Annotated[str, BeforeValidator(normalize_passage_time)]
PositiveInteger = Annotated[int, Field(gt=0)]


class CandidateLine(CTANRecord):
    """Identify one CTAN line discovered from an origin-to-destination timetable table."""

    upstream_id: Identifier = Field(alias="idlinea")
    code: Label = Field(alias="codigo")


class LineMetadata(CTANRecord):
    """Map a CTAN line identifier to its provider-owned transport-mode label."""

    upstream_id: Identifier = Field(alias="idLinea")
    mode: Label = Field(alias="modo")


class TimetablePlaceGroup(BaseModel):
    """Describe one contiguous population-centre column group in a line timetable direction."""

    colspan: PositiveInteger
    name: Label = Field(alias="nombre")


class TimetableRow(BaseModel):
    """Contain one scheduled line service row and its source-provided note."""

    times: list[PassageTime] = Field(alias="horas")
    note: Annotated[str | None, BeforeValidator(optional_text)] = Field(
        default=None, alias="observaciones"
    )


class TimetablePlanner(BaseModel):
    """Contain the paired directions and grouped timetable rows for one CTAN planner."""

    outbound_groups: list[TimetablePlaceGroup] = Field(alias="nucleosIda")
    inbound_groups: list[TimetablePlaceGroup] = Field(alias="nucleosVuelta")
    outbound_rows: list[TimetableRow] = Field(alias="horarioIda")
    inbound_rows: list[TimetableRow] = Field(alias="horarioVuelta")
