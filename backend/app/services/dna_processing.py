"""
Classical DNA sequence processing utilities.

This module contains ONLY classical string/bioinformatics logic.
No Qiskit imports belong here – quantum circuit construction lives in
app/services/quantum_search.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VALID_BASES: frozenset[str] = frozenset("ACGT")
COMPLEMENT: dict[str, str] = {"A": "T", "T": "A", "C": "G", "G": "C"}


@dataclass
class SequenceStats:
    """Basic statistics computed from a DNA sequence."""

    length: int
    gc_content: float          # fraction 0–1
    base_counts: dict[str, int] = field(default_factory=dict)
    is_valid: bool = True
    invalid_chars: list[str] = field(default_factory=list)


def validate_sequence(sequence: str) -> tuple[bool, list[str]]:
    """Return (is_valid, list_of_invalid_chars) for a DNA string."""
    upper = sequence.upper()
    invalid = sorted({ch for ch in upper if ch not in VALID_BASES})
    return (len(invalid) == 0, invalid)


def compute_stats(sequence: str) -> SequenceStats:
    """Compute length, GC content, and per-base counts."""
    upper = sequence.upper()
    is_valid, invalid_chars = validate_sequence(upper)
    counts = {b: upper.count(b) for b in "ACGT"}
    gc = (counts["G"] + counts["C"]) / len(upper) if upper else 0.0
    return SequenceStats(
        length=len(upper),
        gc_content=round(gc, 4),
        base_counts=counts,
        is_valid=is_valid,
        invalid_chars=invalid_chars,
    )


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of a DNA sequence."""
    return "".join(COMPLEMENT[b] for b in reversed(sequence.upper()))


def find_motif_positions(sequence: str, motif: str) -> list[int]:
    """
    Return all 0-based start positions where *motif* occurs in *sequence*
    (overlapping matches included).
    """
    seq, mot = sequence.upper(), motif.upper()
    positions: list[int] = []
    start = 0
    while True:
        idx = seq.find(mot, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + 1
    return positions


def find_mutations(reference: str, query: str) -> list[dict[str, str | int]]:
    """
    Compare two same-length sequences and return substitution mutations.

    Each returned dict has keys: ``position`` (0-based), ``ref``, ``alt``.
    Raises ``ValueError`` for length mismatch.
    """
    ref, qry = reference.upper(), query.upper()
    if len(ref) != len(qry):
        raise ValueError(
            f"Sequences must be the same length (ref={len(ref)}, query={len(qry)})."
        )
    return [
        {"position": i, "ref": r, "alt": q}
        for i, (r, q) in enumerate(zip(ref, qry))
        if r != q
    ]


# ---------------------------------------------------------------------------
# Sequence comparison (reference vs. sample)
# ---------------------------------------------------------------------------

@dataclass
class MismatchDetail:
    """A single substitution between reference and sample."""

    position: int       # 1-based
    ref_base: str       # uppercase single character
    sample_base: str    # uppercase single character


@dataclass
class ComparisonResult:
    """Full result of a reference-vs-sample positional comparison."""

    reference_length: int
    sample_length: int
    total_mismatches: int
    mutation_percentage: float          # 0–100, rounded to 4 d.p.
    mismatches: list[MismatchDetail]


def compare_sequences(reference: str, sample: str) -> ComparisonResult:
    """
    Compare *reference* against *sample* base by base.

    Rules
    -----
    * Both sequences are uppercased before comparison.
    * Only A/T/G/C are valid; invalid characters raise ``ValueError``.
    * Sequences must have equal length; unequal lengths raise ``ValueError``.
    * Mismatch positions are reported using **1-based** indexing.
    * ``mutation_percentage`` = (mismatches / length) × 100.

    No pathogenicity or clinical significance is inferred.
    """
    ref = reference.upper()
    smp = sample.upper()

    # Validate characters
    ref_ok, ref_bad = validate_sequence(ref)
    smp_ok, smp_bad = validate_sequence(smp)
    errors: list[str] = []
    if not ref_ok:
        errors.append(f"Reference contains invalid characters: {ref_bad}")
    if not smp_ok:
        errors.append(f"Sample contains invalid characters: {smp_bad}")
    if errors:
        raise ValueError("; ".join(errors))

    # Validate equal length
    if len(ref) != len(smp):
        raise ValueError(
            f"Sequences must be the same length for positional comparison "
            f"(reference={len(ref)} bp, sample={len(smp)} bp)."
        )

    mismatches: list[MismatchDetail] = [
        MismatchDetail(position=i + 1, ref_base=r, sample_base=s)
        for i, (r, s) in enumerate(zip(ref, smp))
        if r != s
    ]

    n = len(ref)
    pct = round((len(mismatches) / n) * 100, 4) if n else 0.0

    return ComparisonResult(
        reference_length=len(ref),
        sample_length=len(smp),
        total_mismatches=len(mismatches),
        mutation_percentage=pct,
        mismatches=mismatches,
    )


# ---------------------------------------------------------------------------
# Exact motif search
# ---------------------------------------------------------------------------

@dataclass
class MotifSearchResult:
    """Result of an exact motif search."""

    sequence_length: int
    motif: str                      # uppercased, as searched
    motif_length: int
    match_count: int
    positions: list[int]            # 1-based start positions


def search_motif(sequence: str, motif: str) -> MotifSearchResult:
    """
    Find all occurrences of *motif* in *sequence* (overlapping matches included).

    Rules
    -----
    * Both inputs are uppercased before searching.
    * Only A/T/G/C are valid in both *sequence* and *motif*.
    * An empty sequence or motif raises ``ValueError``.
    * A motif longer than the sequence raises ``ValueError``.
    * Returned positions use **1-based** indexing.
    """
    seq = sequence.upper()
    mot = motif.upper()

    if not seq:
        raise ValueError("Sequence must not be empty.")
    if not mot:
        raise ValueError("Motif must not be empty.")

    seq_ok, seq_bad = validate_sequence(seq)
    mot_ok, mot_bad = validate_sequence(mot)
    errors: list[str] = []
    if not seq_ok:
        errors.append(f"Sequence contains invalid characters: {seq_bad}")
    if not mot_ok:
        errors.append(f"Motif contains invalid characters: {mot_bad}")
    if errors:
        raise ValueError("; ".join(errors))

    if len(mot) > len(seq):
        raise ValueError(
            f"Motif length ({len(mot)}) exceeds sequence length ({len(seq)})."
        )

    # Sliding-window search with overlapping matches
    positions: list[int] = []
    start = 0
    while True:
        idx = seq.find(mot, start)
        if idx == -1:
            break
        positions.append(idx + 1)   # convert to 1-based
        start = idx + 1

    return MotifSearchResult(
        sequence_length=len(seq),
        motif=mot,
        motif_length=len(mot),
        match_count=len(positions),
        positions=positions,
    )


# ---------------------------------------------------------------------------
# Grover encoding helper (quantum pre-processing; no Qiskit here)
# ---------------------------------------------------------------------------

def encode_sequence_for_grover(sequence: str, target_index: int) -> dict[str, int]:
    """
    Prepare classical metadata required by the Grover circuit builder.

    Returns a dict with:
    - ``n_qubits``: number of address qubits (ceil(log2(len(sequence))))
    - ``target_index``: the marked item index
    - ``database_size``: total number of elements
    """
    import math

    db_size = len(sequence)
    if db_size < 2:
        raise ValueError("Sequence must have at least 2 characters for Grover search.")
    if not (0 <= target_index < db_size):
        raise ValueError(f"target_index {target_index} out of range [0, {db_size}).")
    n_qubits = math.ceil(math.log2(db_size))
    return {
        "n_qubits": n_qubits,
        "target_index": target_index,
        "database_size": db_size,
    }
