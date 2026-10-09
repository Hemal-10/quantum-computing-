"""Pydantic request and response schemas for the DNA analysis endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, computed_field


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_VALID_BASES = frozenset("ACGTacgt")


def _validate_dna_field(value: str, field_label: str) -> str:
    """Strip whitespace, ensure non-empty, then check for invalid characters."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_label} must not be empty.")
    invalid = sorted({ch for ch in stripped.upper() if ch not in frozenset("ACGT")})
    if invalid:
        raise ValueError(
            f"{field_label} contains invalid characters: {invalid}. "
            "Only A, T, G, C are accepted."
        )
    return stripped


# ---------------------------------------------------------------------------
# POST /api/dna/compare
# ---------------------------------------------------------------------------

class CompareRequest(BaseModel):
    """Request body for sequence comparison."""

    reference: str = Field(
        ...,
        min_length=1,
        description="Reference DNA sequence (A/T/G/C only, case-insensitive).",
        examples=["ACGTACGT"],
    )
    sample: str = Field(
        ...,
        min_length=1,
        description="Sample DNA sequence to compare against the reference.",
        examples=["ACTTACGT"],
    )

    @field_validator("reference", mode="before")
    @classmethod
    def validate_reference(cls, v: str) -> str:
        return _validate_dna_field(v, "Reference")

    @field_validator("sample", mode="before")
    @classmethod
    def validate_sample(cls, v: str) -> str:
        return _validate_dna_field(v, "Sample")


class MismatchItem(BaseModel):
    """A single base-pair mismatch between reference and sample."""

    position: int = Field(..., description="1-based position in the alignment.")
    ref_base: str = Field(..., description="Reference base at this position.")
    sample_base: str = Field(..., description="Sample base at this position.")

    @computed_field
    @property
    def reference_base(self) -> str:
        """Alias for ref_base ensuring frontend compatibility."""
        return self.ref_base


class CompareResponse(BaseModel):
    """Response body for POST /api/dna/compare."""

    reference_length: int = Field(..., description="Length of the reference sequence (bp).")
    sample_length: int = Field(..., description="Length of the sample sequence (bp).")
    total_mismatches: int = Field(..., description="Number of differing positions.")
    mutation_percentage: float = Field(
        ...,
        description="Percentage of positions that differ (0–100), rounded to 4 d.p.",
    )
    mismatches: list[MismatchItem] = Field(
        default_factory=list,
        description="List of mismatches with 1-based positions and bases.",
    )


# ---------------------------------------------------------------------------
# POST /api/dna/motif
# ---------------------------------------------------------------------------

class MotifRequest(BaseModel):
    """Request body for exact motif search."""

    sequence: str = Field(
        ...,
        min_length=1,
        description="DNA sequence to search within (A/T/G/C only, case-insensitive).",
        examples=["ACGTACGTACGT"],
    )
    motif: str = Field(
        ...,
        min_length=1,
        description="Exact motif pattern to search for (A/T/G/C only, case-insensitive).",
        examples=["CGT"],
    )

    @field_validator("sequence", mode="before")
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        return _validate_dna_field(v, "Sequence")

    @field_validator("motif", mode="before")
    @classmethod
    def validate_motif(cls, v: str) -> str:
        return _validate_dna_field(v, "Motif")


class MotifResponse(BaseModel):
    """Response body for POST /api/dna/motif."""

    sequence_length: int = Field(..., description="Length of the searched sequence (bp).")
    motif: str = Field(..., description="Motif searched for (uppercased).")
    motif_length: int = Field(..., description="Length of the motif.")
    match_count: int = Field(..., description="Total number of occurrences found.")
    positions: list[int] = Field(
        default_factory=list,
        description="1-based start positions of all occurrences (overlapping included).",
    )
