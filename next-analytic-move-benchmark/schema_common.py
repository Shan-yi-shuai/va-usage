from __future__ import annotations

import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, constr, field_validator, model_validator


OthersString = constr(
    pattern=r"^others\(.+\)$"
)
"""
A constrained string for taxonomy escape hatch.
Format must be: others(<non-empty description>), e.g., "others(domain-specific logs)".
"""


IdentifierString = constr(
    pattern=r"^[a-z0-9]+(?:[._:-][a-z0-9]+)*$"
)
"""
A constrained identifier string for stable references.
Use lower-case ASCII tokens separated by `.`, `_`, `-`, or `:`.
Examples: "timeline-view", "panel.control", "view:details".
"""


NameSource = Literal[
    "explicit",
    "caption",
    "inferred",
    "generated",
]
"""
How a human-readable name was obtained.
"""


def _slugify_identifier(value: Optional[str], fallback: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"['’]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or fallback


def _dedupe_strings(values: Optional[List[str]]) -> Optional[List[str]]:
    if not values:
        return None

    result: List[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        cleaned = str(value).strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(cleaned)
    return result or None


def _make_unique_identifier(candidate: str, seen: set[str]) -> str:
    if candidate not in seen:
        seen.add(candidate)
        return candidate

    suffix = 2
    while True:
        updated = f"{candidate}-{suffix}"
        if updated not in seen:
            seen.add(updated)
            return updated
        suffix += 1


class ViewRef(BaseModel):
    """Stable canonical reference to a view or sub-view."""

    viewId: IdentifierString = Field(
        ...,
        description="Canonical identifier of the parent view.",
    )

    subViewId: Optional[IdentifierString] = Field(
        default=None,
        description="Canonical identifier of the sub-view when the reference points below view level.",
    )


class CapabilityRef(BaseModel):
    """Stable canonical reference to a sub-view capability."""

    viewId: IdentifierString = Field(
        ...,
        description="Canonical identifier of the parent view.",
    )

    subViewId: IdentifierString = Field(
        ...,
        description="Canonical identifier of the parent sub-view.",
    )

    capabilityId: IdentifierString = Field(
        ...,
        description="Canonical identifier of the referenced capability.",
    )


class CoordinationRef(BaseModel):
    """Stable canonical reference to a coordination, with optional local note."""

    coordinationId: IdentifierString = Field(
        ...,
        description="Canonical coordination identifier from the system specification.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Optional short note about how the referencing schema uses this coordination.",
    )


class EvidenceReference(BaseModel):
    """Evidence attached to an extracted item for verification and error analysis."""

    passageIds: Optional[List[int]] = Field(
        default=None,
        description="Ordered passage identifiers that support this extraction, if tracked.",
    )

    figureRefs: Optional[List[str]] = Field(
        default=None,
        description="Figure references such as 'Fig. 1a' or local image file names.",
    )

    quotes: Optional[List[str]] = Field(
        default=None,
        description="Short supporting quotes or evidence snippets.",
    )

    reasoning: Optional[str] = Field(
        default=None,
        description="Brief explanation of how the evidence supports the structured item.",
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score for the extracted item.",
    )

    @field_validator("figureRefs", "quotes", mode="before")
    @classmethod
    def normalize_text_lists(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        self.figureRefs = _dedupe_strings(self.figureRefs)
        self.quotes = _dedupe_strings(self.quotes)
        if not self.passageIds and not self.figureRefs and not self.quotes:
            raise ValueError(
                "EvidenceReference requires at least one of passageIds, figureRefs, or quotes."
            )
        return self
