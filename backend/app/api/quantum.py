"""
Quantum search API router.

Endpoints
---------
POST /api/quantum/grover  – Run Grover's algorithm on a set of candidate indices.

This router delegates all circuit construction and simulation to
``app.services.quantum_search.GroverEngine``.  Classical DNA pre-processing
(motif positions, mismatch positions) is the caller's responsibility and is
handled by the DNA endpoints (app/api/dna.py).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.quantum import GroverRequest, GroverResponse
from app.services.quantum_search import GroverEngine

router = APIRouter(prefix="/api/quantum", tags=["quantum"])


@router.post(
    "/grover",
    response_model=GroverResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Grover's algorithm on candidate DNA position indices",
    description=(
        "Executes Grover's search algorithm on **AerSimulator** "
        "(a local quantum circuit simulator — not real hardware).\n\n"
        "### Workflow\n"
        "1. Classical layer (``/api/dna/compare`` or ``/api/dna/motif``) "
        "   returns candidate position indices and a set of marked positions.\n"
        "2. This endpoint takes those two lists and runs Grover's algorithm to "
        "   amplify the probability of measuring a marked index.\n\n"
        "### Oracle predicate\n"
        "**\"Is this candidate index in the marked set?\"**\n\n"
        "### Limitations\n"
        "- Results are statistical; probabilities come from measurement counts.\n"
        "- No pathogenicity or clinical significance is inferred.\n"
        "- This does **not** demonstrate real-world quantum speedup.\n"
    ),
)
async def run_grover(body: GroverRequest) -> GroverResponse:
    """Run Grover's algorithm on the provided candidate and marked indices."""
    try:
        engine = GroverEngine(
            candidate_indices=body.candidate_indices,
            marked_indices=body.marked_indices,
            shots=body.shots,
        )
        result = engine.run()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        # Catch any unexpected Qiskit/Aer errors and surface them as 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation error: {exc}",
        ) from exc

    return GroverResponse(
        candidate_indices=result.candidate_indices,
        marked_indices=result.marked_indices,
        n_search_qubits=result.n_search_qubits,
        n_grover_iterations=result.n_grover_iterations,
        shots=result.shots,
        circuit_depth=result.circuit_depth,
        circuit_width=result.circuit_width,
        raw_counts=result.raw_counts,
        decoded_counts=result.decoded_counts,
        top_index=result.top_index,
        top_count=result.top_count,
        top_index_in_marked=result.top_index_in_marked,
        empirical_success_probability=result.empirical_success_probability,
        marked_total_counts=result.marked_total_counts,
        marked_empirical_probability=result.marked_empirical_probability,
        simulator_note=result.simulator_note,
    )
