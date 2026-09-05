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
