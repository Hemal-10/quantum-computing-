"""
Quantum search engine using Qiskit Grover's Algorithm.

DNA-search context
------------------
In the DNA candidate-search task, a *candidate* is a 0-based position index
(into a reference or sample sequence) that a classical pre-processing step has
nominated as potentially mutated or as a motif-match location.  Grover's
algorithm searches these candidate positions to find which ones satisfy a
predicate (here: "is this index in the marked set?").

IMPORTANT simulator limitations
---------------------------------
* This engine runs on ``AerSimulator``, a local state-vector/stabilizer
  simulator.  It does **not** run on quantum hardware.
* The maximum practical search space is bounded by available RAM.
  A state-vector simulation of n qubits requires 2^n complex amplitudes
  (16 bytes each): n=20 needs ~16 MB, n=30 needs ~16 GB.
* Results are statistical: measurement counts vary across runs.  All
  probabilities reported here are *empirical* (counts / shots) and do NOT
  prove quantum speedup on real hardware.
* No claim of real-world genomic advantage is made or implied.

Module structure
----------------
Layer 1 – Low-level circuit builders:
    ``_build_multi_oracle``  – phase oracle for an arbitrary set of targets
    ``_build_diffuser``      – Grover diffusion operator
    ``_decode_bitstring``    – canonical big-endian → integer decoding

Layer 2 – Search-space helpers:
    ``_min_qubits``          – minimum qubits for a given database size
    ``_iteration_count``     – optimal iterations for k solutions in N items

Layer 3 – High-level engine:
    ``GroverEngine``         – dataclass that runs a complete Grover search
    ``run_grover_search``    – backward-compatible single-target wrapper
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Maximum qubits the engine will accept (guards against OOM).
MAX_QUBITS: int = 20

#: Default number of simulator shots.
DEFAULT_SHOTS: int = 1024


# ===========================================================================
# Layer 1 – Low-level circuit builders
# ===========================================================================

def _decode_bitstring(bitstring: str) -> int:
    """
    Convert an AerSimulator measurement bitstring to an integer index.

    Qiskit Aer returns measurement results in **big-endian** order:
    the leftmost character is the *highest-index* classical bit, and
    the rightmost character is classical bit 0 (the LSB of the integer).

    Example (3 qubits, target = 5 = 0b101):
        Qiskit counts key → "101"
        int("101", 2)     → 5  ✓

    This function exists so that the decoding convention is explicit,
    documented, and independently tested.
    """
    return int(bitstring, 2)


def _build_multi_oracle(n_qubits: int, marked_indices: frozenset[int]) -> QuantumCircuit:
    """
    Build a phase oracle that flips the phase of every state in *marked_indices*.

    For each marked index the oracle applies X-gates to zero-bits, then a
    multi-controlled-Z (MCZ), then un-applies the X-gates.  Each marked
    index adds one MCZ gadget.

    Encoding convention (explicit, tested):
        qubit 0  = least-significant bit (LSB)  of the binary index
        qubit n-1 = most-significant bit (MSB)
        AerSimulator reads classical bits right-to-left (big-endian),
        so bit 0 maps to the *rightmost* character in the measurement string.

    Parameters
    ----------
    n_qubits:       Number of address qubits.
    marked_indices: Set of 0-based integer indices to mark.
    """
    qr = QuantumRegister(n_qubits, "q")
    oracle = QuantumCircuit(qr, name="Oracle")

    for target in sorted(marked_indices):
        # Build the bit pattern for this target (LSB at position 0)
        bits = format(target, f"0{n_qubits}b")[::-1]   # LSB first

        # Flip qubits whose bit is '0' so the MCZ fires on |11…1⟩
        zeros = [i for i, b in enumerate(bits) if b == "0"]
        if zeros:
            oracle.x([qr[i] for i in zeros])

        # Multi-controlled Z
        if n_qubits == 1:
            oracle.z(qr[0])
        else:
            oracle.h(qr[-1])
            oracle.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            oracle.h(qr[-1])

        # Undo the X-flips
        if zeros:
            oracle.x([qr[i] for i in zeros])

    return oracle


def _build_diffuser(n_qubits: int) -> QuantumCircuit:
    """
    Build the Grover diffusion operator  2|s⟩⟨s| − I.

    Steps:
      1. H⊗n                 (rotate to computational basis)
      2. X⊗n                 (shift |0⟩ to |1⟩)
      3. MCZ on |11…1⟩       (phase flip on the all-ones state)
      4. X⊗n  (undo)
      5. H⊗n  (rotate back to Hadamard basis)
    """
    qr = QuantumRegister(n_qubits, "q")
    diffuser = QuantumCircuit(qr, name="Diffuser")

    diffuser.h(qr)
    diffuser.x(qr)

    if n_qubits == 1:
        diffuser.z(qr[0])
    else:
        diffuser.h(qr[-1])
        diffuser.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        diffuser.h(qr[-1])

    diffuser.x(qr)
    diffuser.h(qr)

    return diffuser


# ===========================================================================
# Layer 2 – Search-space helpers
# ===========================================================================

def _min_qubits(database_size: int) -> int:
    """
    Return the minimum number of qubits needed to address *database_size* items.

    Uses ceil(log2(database_size)).  A database of exactly 1 item requires
    1 qubit (special case to avoid log2(1)=0).
    """
    if database_size <= 1:
        return 1
    return math.ceil(math.log2(database_size))


def _iteration_count(n_qubits: int, n_solutions: int) -> int:
    """
    Calculate the theoretically optimal number of Grover iterations.

    Formula:  k ≈ (π / 4) × sqrt(N / M)
    where N = 2^n_qubits (search space size) and M = n_solutions.

    Edge cases
    ----------
    * n_solutions == 0: no marked items; return 0 (skip all iterations).
    * n_solutions >= N/2: the amplitude amplification gain is small or
      negative; return 1 to avoid over-rotation.
    * Result is always at least 1 for any M in [1, N/2).
    """
    n_space = 2 ** n_qubits

    if n_solutions <= 0:
        return 0

    if n_solutions >= n_space:
        # All states are marked; trivially return 0 iterations.
        return 0

    if n_solutions >= n_space / 2:
        # Danger zone: too many solutions for amplitude amplification.
        return 1

    theta = math.asin(math.sqrt(n_solutions / n_space))
    if theta == 0:
        return 0
    k = (math.pi / (4 * theta)) - 0.5
    return max(1, round(k))


# ===========================================================================
# Layer 3 – High-level engine
# ===========================================================================

@dataclass
class GroverSearchResult:
    """
    Complete result of a Grover search run.

    All probabilities are empirical (counts / shots), derived entirely
    from AerSimulator measurement results.  No value is hardcoded.
    """

    # --- Input parameters ---
    candidate_indices: list[int]      = field(default_factory=list)
    marked_indices: list[int]         = field(default_factory=list)
    n_search_qubits: int              = 0
    n_grover_iterations: int          = 0
    shots: int                        = DEFAULT_SHOTS

    # --- Circuit metadata ---
    circuit_depth: int                = 0
    circuit_width: int                = 0   # == n_search_qubits

    # --- Raw simulation outputs ---
    raw_counts: dict[str, int]        = field(default_factory=dict)

    # --- Decoded results ---
    decoded_counts: dict[int, int]    = field(default_factory=dict)
    top_index: int | None             = None
    top_count: int                    = 0
    top_index_in_marked: bool         = False

    # --- Empirical statistics ---
    empirical_success_probability: float  = 0.0
    marked_total_counts: int              = 0
    marked_empirical_probability: float   = 0.0

    # --- Simulator note ---
    simulator_note: str = (
        "Results are from AerSimulator (local state-vector simulator). "
        "This is NOT real quantum hardware and does NOT demonstrate "
        "a real-world genomic speedup."
    )


class GroverEngine:
    """
    Grover search engine for a finite set of candidate DNA position indices.

    Usage
    -----
    ::

        engine = GroverEngine(
            candidate_indices=[0, 3, 7, 12, 15],   # positions to search
            marked_indices=[7, 15],                 # positions satisfying predicate
        )
        result = engine.run(shots=2048)

    The *candidate_indices* list defines the finite search space.  The
    minimum number of qubits is chosen automatically via ``_min_qubits``.
    Only indices that appear in *marked_indices* AND are within the qubit
    address space are marked in the oracle.

    Predicate
    ---------
    The oracle predicate is: "is this position index in *marked_indices*?"
    In the DNA context *marked_indices* is provided by the classical layer
    (e.g. mismatch positions from ``compare_sequences``), and Grover's
    algorithm is used to amplify the probability of measuring a marked index.
    """

    def __init__(
        self,
        candidate_indices: Sequence[int],
        marked_indices: Sequence[int],
        shots: int = DEFAULT_SHOTS,
    ) -> None:
        if not candidate_indices:
            raise ValueError("candidate_indices must not be empty.")
        if any(i < 0 for i in candidate_indices):
            raise ValueError("All candidate indices must be non-negative integers.")
        if shots < 1:
            raise ValueError(f"shots must be >= 1, got {shots}.")

        self._candidates = sorted(set(candidate_indices))
        self._marked = frozenset(marked_indices) & frozenset(self._candidates)
        self._shots = shots

        # Database size is the total search space (next power of 2 >= max index + 1)
        max_idx = max(self._candidates)
        db_size = max(max_idx + 1, len(self._candidates))
        self._n_qubits = _min_qubits(db_size)

        if self._n_qubits > MAX_QUBITS:
            raise ValueError(
                f"Search space requires {self._n_qubits} qubits, which exceeds "
                f"the engine limit of {MAX_QUBITS}.  Reduce the candidate set."
            )

        self._n_iter = _iteration_count(self._n_qubits, len(self._marked))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def build_circuit(self) -> QuantumCircuit:
        """Return the full Grover circuit (without measurement, for inspection)."""
        qr = QuantumRegister(self._n_qubits, "q")
        circuit = QuantumCircuit(qr)
        circuit.h(qr)

        if self._n_iter > 0 and self._marked:
            oracle = _build_multi_oracle(self._n_qubits, self._marked)
            diffuser = _build_diffuser(self._n_qubits)
            for _ in range(self._n_iter):
                circuit.compose(oracle, inplace=True)
                circuit.compose(diffuser, inplace=True)

        return circuit

    def run(self, shots: int | None = None) -> GroverSearchResult:
        """
        Build the circuit, simulate on AerSimulator, and return results.

        Parameters
        ----------
        shots: Override the shot count set in __init__.

        Returns
        -------
        GroverSearchResult with real measurement counts and decoded indices.
        """
        n_shots = shots if shots is not None else self._shots

        # Build and measure
        qr = QuantumRegister(self._n_qubits, "q")
        cr = ClassicalRegister(self._n_qubits, "c")
        circuit = QuantumCircuit(qr, cr)
        circuit.h(qr)

        if self._n_iter > 0 and self._marked:
            oracle = _build_multi_oracle(self._n_qubits, self._marked)
            diffuser = _build_diffuser(self._n_qubits)
            for _ in range(self._n_iter):
                circuit.compose(oracle, inplace=True)
                circuit.compose(diffuser, inplace=True)

        circuit.measure(qr, cr)

        # Simulate
        simulator = AerSimulator()
        job = simulator.run(circuit, shots=n_shots)
        sim_result = job.result()
        raw_counts: dict[str, int] = sim_result.get_counts()

        # Decode bitstrings → integer indices
        decoded_counts: dict[int, int] = {
            _decode_bitstring(bs): cnt for bs, cnt in raw_counts.items()
        }

        # Identify the top-measured index
        if decoded_counts:
            top_index, top_count = max(decoded_counts.items(), key=lambda kv: kv[1])
        else:
            top_index, top_count = None, 0

        # Empirical statistics
        marked_total = sum(
            cnt for idx, cnt in decoded_counts.items()
            if idx in self._marked
        )
        emp_success = round(marked_total / n_shots, 6) if n_shots else 0.0
        top_in_marked = (top_index in self._marked) if top_index is not None else False

        return GroverSearchResult(
            candidate_indices=self._candidates,
            marked_indices=sorted(self._marked),
            n_search_qubits=self._n_qubits,
            n_grover_iterations=self._n_iter,
            shots=n_shots,
            circuit_depth=circuit.depth(),
            circuit_width=circuit.num_qubits,
            raw_counts=raw_counts,
            decoded_counts=decoded_counts,
            top_index=top_index,
            top_count=top_count,
            top_index_in_marked=top_in_marked,
            empirical_success_probability=round(top_count / n_shots, 6) if n_shots else 0.0,
            marked_total_counts=marked_total,
            marked_empirical_probability=emp_success,
        )


# ===========================================================================
# Backward-compatible single-target wrapper (used by earlier tests)
# ===========================================================================

@dataclass
class GroverResult:
    """
    Legacy single-target result dataclass.

    Retained for backward compatibility with the original foundation-phase
    tests and the encode_sequence_for_grover helper in dna_processing.py.
    New code should use ``GroverEngine`` and ``GroverSearchResult`` instead.
    """
    target_index: int
    n_qubits: int
    n_iterations: int
    shots: int
    counts: dict[str, int]        = field(default_factory=dict)
    top_state: str                 = ""
    top_count: int                 = 0
    success_probability: float     = 0.0


def run_grover_search(
    n_qubits: int,
    target_index: int,
    shots: int = DEFAULT_SHOTS,
) -> GroverResult:
    """
    Backward-compatible single-target Grover search.

    Delegates to ``GroverEngine`` internally so the same circuit-building
    and decoding code is exercised.  This function is preserved so any
    existing callers continue to work without modification.
    """
    engine = GroverEngine(
        candidate_indices=list(range(2 ** n_qubits)),
        marked_indices=[target_index],
        shots=shots,
    )
    result = engine.run(shots=shots)

    top_state = max(result.raw_counts, key=lambda k: result.raw_counts[k]) if result.raw_counts else ""
    top_count = result.raw_counts.get(top_state, 0)

    return GroverResult(
        target_index=target_index,
        n_qubits=n_qubits,
        n_iterations=result.n_grover_iterations,
        shots=shots,
        counts=result.raw_counts,
        top_state=top_state,
        top_count=top_count,
        success_probability=round(top_count / shots, 4) if shots else 0.0,
    )


# ---------------------------------------------------------------------------
# Convenience builders (also used by the oracle in the original phase)
# ---------------------------------------------------------------------------

def build_grover_oracle(n_qubits: int, target_index: int) -> QuantumCircuit:
    """Single-target oracle shim kept for API compatibility."""
    return _build_multi_oracle(n_qubits, frozenset({target_index}))


def build_diffuser(n_qubits: int) -> QuantumCircuit:
    """Diffuser shim kept for API compatibility."""
    return _build_diffuser(n_qubits)


def optimal_iterations(n_qubits: int) -> int:
    """Single-solution iteration count shim kept for API compatibility."""
    return _iteration_count(n_qubits, 1)
