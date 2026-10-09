"""DNA analysis API router.

Endpoints
---------
POST /api/dna/compare  – positional reference-vs-sample comparison
POST /api/dna/motif    – exact motif search with overlapping matches

This router is completely independent of Qiskit.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.dna import (
    CompareRequest,
    CompareResponse,
    MismatchItem,
    MotifRequest,
    MotifResponse,
)
from app.services.dna_processing import compare_sequences, search_motif

router = APIRouter(prefix="/api/dna", tags=["dna"])


# ---------------------------------------------------------------------------
# POST /api/dna/compare
# ---------------------------------------------------------------------------

@router.post(
    "/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare reference and sample DNA sequences",
    description=(
        "Performs a base-by-base positional comparison between a reference and "
        "a sample sequence of equal length. Returns all mismatch positions using "
        "**1-based** indexing together with the reference base, sample base, "
        "total mismatch count, and mutation percentage.\n\n"
        "> ⚠ No pathogenicity or clinical significance is inferred."
    ),
)
async def compare_dna(body: CompareRequest) -> CompareResponse:
    """Positional comparison of two equal-length DNA sequences."""
    try:
        result = compare_sequences(body.reference, body.sample)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return CompareResponse(
        reference_length=result.reference_length,
        sample_length=result.sample_length,
        total_mismatches=result.total_mismatches,
        mutation_percentage=result.mutation_percentage,
        mismatches=[
            MismatchItem(
                position=m.position,
                ref_base=m.ref_base,
                sample_base=m.sample_base,
            )
            for m in result.mismatches
        ],
    )


# ---------------------------------------------------------------------------
# POST /api/dna/motif
# ---------------------------------------------------------------------------

@router.post(
    "/motif",
    response_model=MotifResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for an exact motif in a DNA sequence",
    description=(
        "Finds all exact occurrences of *motif* within *sequence*, "
        "including overlapping matches. Positions are **1-based**. "
        "Returns an empty list when the motif is absent."
    ),
)
async def search_dna_motif(body: MotifRequest) -> MotifResponse:
    """Exact motif search with overlapping matches."""
    try:
        result = search_motif(body.sequence, body.motif)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return MotifResponse(
        sequence_length=result.sequence_length,
        motif=result.motif,
        motif_length=result.motif_length,
        match_count=result.match_count,
        positions=result.positions,
    )
