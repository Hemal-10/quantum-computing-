"""
Pydantic request and response schemas for the Grover quantum search endpoint.

POST /api/quantum/grover
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.quantum_search import DEFAULT_SHOTS, MAX_QUBITS


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class GroverRequest(BaseModel):
    """
    Request body for POST /api/quantum/grover.

    The caller provides:
    - ``candidate_indices``: the finite set of 0-based position indices to
      search (e.g. mismatch positions from the classical comparison step).
    - ``marked_indices``: the subset that satisfies the search predicate
      (e.g. positions that are also mutation hot-spots or motif start sites).
    - ``shots``: number of AerSimulator measurement shots (optional).

    The oracle predicate is:
        "is this candidate index in the marked set?"
    """

    candidate_indices: list[int] = Field(
        ...,
        min_length=1,
        description=(
            "Finite set of 0-based position indices to search over. "
            "Must be non-empty and contain only non-negative integers."
        ),
        examples=[[0, 1, 2, 3, 4, 5, 6, 7]],
    )
    marked_indices: list[int] = Field(
        default_factory=list,
        description=(
            "Subset of candidate_indices that satisfies the search predicate. "
            "An empty list is allowed (no solutions); Grover iterations are "
            "skipped and the result is a uniform distribution."
        ),
        examples=[[3, 7]],
    )
    shots: int = Field(
        default=DEFAULT_SHOTS,
        ge=1,
        le=65536,
        description=f"Number of AerSimulator measurement shots (1–65536). Default {DEFAULT_SHOTS}.",
    )

    @field_validator("candidate_indices", mode="before")
    @classmethod
    def validate_candidates(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("candidate_indices must not be empty.")
        if any(not isinstance(i, int) or i < 0 for i in v):
            raise ValueError("All candidate_indices must be non-negative integers.")
        return v

    @field_validator("marked_indices", mode="before")
    @classmethod
    def validate_marked(cls, v: list[int]) -> list[int]:
        if any(not isinstance(i, int) or i < 0 for i in v):
            raise ValueError("All marked_indices must be non-negative integers.")
        return v

    @model_validator(mode="after")
    def validate_space_size(self) -> "GroverRequest":
        """Guard against search spaces that exceed the engine's qubit limit."""
        import math
        max_idx = max(self.candidate_indices)
        db_size = max(max_idx + 1, len(self.candidate_indices))
        n_qubits = math.ceil(math.log2(max(db_size, 2)))
        if n_qubits > MAX_QUBITS:
            raise ValueError(
                f"The candidate set requires {n_qubits} qubits, which exceeds "
                f"the engine limit of {MAX_QUBITS}.  Use a smaller candidate set."
            )
        return self


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class GroverResponse(BaseModel):
    """
    Response body for POST /api/quantum/grover.

    All probabilities are empirical (counts / shots) derived directly from
    AerSimulator measurements.  No value is hardcoded.
    """

    # --- Input echo ---
    candidate_indices: list[int] = Field(
        ..., description="The candidate indices that were searched."
    )
    marked_indices: list[int] = Field(
        ..., description="The marked indices (satisfying the predicate)."
    )

    # --- Circuit metadata ---
    n_search_qubits: int = Field(
        ..., description="Number of address qubits used in the circuit."
    )
    n_grover_iterations: int = Field(
        ..., description="Number of Grover (oracle + diffuser) iterations applied."
    )
    shots: int = Field(..., description="Total measurement shots used.")
    circuit_depth: int = Field(..., description="Gate depth of the final circuit.")
    circuit_width: int = Field(..., description="Number of qubits in the circuit.")

    # --- Raw simulation output ---
    raw_counts: dict[str, int] = Field(
        ...,
        description=(
            "Raw measurement bitstring → count dictionary from AerSimulator. "
            "Bitstrings are big-endian (leftmost char = highest qubit index)."
        ),
    )

    # --- Decoded results ---
    decoded_counts: dict[int, int] = Field(
        ...,
        description="Measurement counts keyed by decoded integer index.",
    )
    top_index: int | None = Field(
        ...,
        description="The most-frequently measured candidate index (None if no shots).",
    )
    top_count: int = Field(..., description="Measurement count for top_index.")
    top_index_in_marked: bool = Field(
        ..., description="Whether top_index is one of the marked solutions."
    )

    # --- Empirical statistics ---
    empirical_success_probability: float = Field(
        ...,
        description=(
            "Fraction of shots that measured top_index. "
            "Derived from simulation; not hardcoded."
        ),
    )
    marked_total_counts: int = Field(
        ..., description="Total shots that measured any marked index."
    )
    marked_empirical_probability: float = Field(
        ...,
        description=(
            "Fraction of shots that measured any marked index. "
            "Derived from simulation; not hardcoded."
        ),
    )

    # --- Disclaimer ---
    simulator_note: str = Field(
        ...,
        description=(
            "Reminder that this is a local AerSimulator result, not real "
            "quantum hardware, and does not demonstrate a real-world speedup."
        ),
    )
