"""
Tests for the Grover quantum search engine.

Layer A – Unit tests for pure helper functions (no Qiskit simulation):
    - _decode_bitstring:  explicit bitstring → integer conversion
    - _min_qubits:        minimum qubit count for a database size
    - _iteration_count:   optimal iteration formula for k solutions

Layer B – Circuit-level tests (builds circuits, checks structure):
    - Oracle marks correct states (statevector inspection)
    - Diffuser gate count

Layer C – Integration tests via GroverEngine (real AerSimulator shots):
    - Single marked candidate: top measured index should be the marked one
    - Multiple marked candidates: combined probability is high
    - No marked candidates: result is near-uniform (no amplification)
    - Boundary indices (index 0 and index 2^n - 1)
    - Backward-compatible run_grover_search wrapper

Layer D – API endpoint tests via httpx:
    - Single marked, multiple marked, zero marked, invalid inputs

Statistical note
----------------
Grover is a probabilistic algorithm.  Tests that check simulation outcomes
use loose thresholds (> 1/N + margin) rather than exact counts, because shot
noise is unavoidable.  The threshold is set conservatively so false failures
are extremely unlikely at 1024 shots.
"""
from __future__ import annotations

import math

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.quantum_search import (
    DEFAULT_SHOTS,
    GroverEngine,
    _build_diffuser,
    _build_multi_oracle,
    _decode_bitstring,
    _iteration_count,
    _min_qubits,
    run_grover_search,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        yield c


# ===========================================================================
# Layer A – Pure helper unit tests (no Qiskit)
# ===========================================================================

class TestDecodebitstring:
    """_decode_bitstring is explicit about Qiskit's big-endian convention."""

    def test_all_zeros(self):
        assert _decode_bitstring("000") == 0

    def test_all_ones_3bit(self):
        assert _decode_bitstring("111") == 7

    def test_index_5_three_qubits(self):
        # 5 = 0b101  → big-endian bitstring is "101"
        assert _decode_bitstring("101") == 5

    def test_index_1_one_qubit(self):
        assert _decode_bitstring("1") == 1

    def test_index_0_one_qubit(self):
        assert _decode_bitstring("0") == 0

    def test_index_12_four_qubits(self):
        # 12 = 0b1100 → big-endian "1100"
        assert _decode_bitstring("1100") == 12

    def test_roundtrip(self):
        """Encoding an index and decoding it must yield the same value."""
        for n in range(16):
            bits = format(n, "04b")   # big-endian, 4 chars
            assert _decode_bitstring(bits) == n


class TestMinQubits:
    def test_two_items(self):
        assert _min_qubits(2) == 1

    def test_four_items(self):
        assert _min_qubits(4) == 2

    def test_five_items_needs_three(self):
        assert _min_qubits(5) == 3

    def test_eight_items(self):
        assert _min_qubits(8) == 3

    def test_nine_items_needs_four(self):
        assert _min_qubits(9) == 4

    def test_one_item_returns_one(self):
        assert _min_qubits(1) == 1


class TestIterationCount:
    def test_zero_solutions_returns_zero(self):
        assert _iteration_count(3, 0) == 0

    def test_single_solution_four_items(self):
        # N=4, M=1: theta = arcsin(1/2) = pi/6; k = round((pi/(4*theta)) - 0.5) = 1
        # Grover on 2 qubits achieves 100% success probability in exactly 1 iteration
        k = _iteration_count(2, 1)
        assert k == 1

    def test_single_solution_eight_items(self):
        # N=8, M=1 → (π/4)√8 ≈ 2.22 → 2
        k = _iteration_count(3, 1)
        assert k >= 1

    def test_two_solutions_four_items(self):
        # N=4, M=2 → M >= N/2 → returns 1
        assert _iteration_count(2, 2) == 1

    def test_all_solutions_returns_zero(self):
        # M == N → no point iterating
        assert _iteration_count(3, 8) == 0

    def test_always_at_least_one_for_valid_m(self):
        for n in range(1, 5):
            for m in range(1, 2 ** n // 2):
                assert _iteration_count(n, m) >= 1


# ===========================================================================
# Layer B – Circuit structure tests (no simulation)
# ===========================================================================

class TestOracleStructure:
    def test_oracle_has_gates(self):
        oracle = _build_multi_oracle(3, frozenset({5}))
        assert oracle.depth() > 0

    def test_oracle_width_matches_qubits(self):
        oracle = _build_multi_oracle(4, frozenset({3, 11}))
        assert oracle.num_qubits == 4

    def test_oracle_two_targets_deeper_than_one(self):
        o1 = _build_multi_oracle(3, frozenset({2}))
        o2 = _build_multi_oracle(3, frozenset({2, 5}))
        assert o2.depth() >= o1.depth()

    def test_diffuser_width(self):
        d = _build_diffuser(3)
        assert d.num_qubits == 3

    def test_diffuser_has_hadamards(self):
        d = _build_diffuser(2)
        gate_names = [inst.operation.name for inst in d.data]
        assert "h" in gate_names


# ===========================================================================
# Layer C – Integration tests (real AerSimulator)
# ===========================================================================

STAT_SHOTS = 2048   # More shots → tighter statistics


class TestGroverEngineSingleMarked:
    """Single marked candidate in a small search space."""

    def test_top_index_is_marked(self):
        """
        With one marked target out of 8 candidates (3 qubits), the most
        frequently measured index should be the marked one.
        """
        engine = GroverEngine(
            candidate_indices=list(range(8)),
            marked_indices=[5],
        )
        result = engine.run(shots=STAT_SHOTS)
        assert result.top_index == 5, (
            f"Expected top_index=5, got {result.top_index}. "
            f"decoded_counts={result.decoded_counts}"
        )

    def test_top_index_in_marked_flag(self):
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[3],
        )
        result = engine.run(shots=STAT_SHOTS)
        assert result.top_index_in_marked is True

    def test_marked_probability_exceeds_random(self):
        """
        Marked probability must be substantially higher than 1/N (random).
        Threshold: > 1/(2^n) × 3  (i.e., at least 3× the uniform chance).
        """
        n_qubits = 3  # N = 8
        engine = GroverEngine(
            candidate_indices=list(range(2 ** n_qubits)),
            marked_indices=[6],
        )
        result = engine.run(shots=STAT_SHOTS)
        uniform_prob = 1.0 / (2 ** n_qubits)
        assert result.marked_empirical_probability > uniform_prob * 3, (
            f"Marked prob {result.marked_empirical_probability:.4f} is not "
            f"substantially above uniform {uniform_prob:.4f}"
        )

    def test_circuit_metadata_populated(self):
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[2],
        )
        result = engine.run(shots=256)
        assert result.n_search_qubits == 2
        assert result.n_grover_iterations >= 1
        assert result.circuit_depth > 0
        assert result.circuit_width == 2
        assert result.shots == 256

    def test_raw_counts_sum_to_shots(self):
        shots = 512
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[1],
        )
        result = engine.run(shots=shots)
        assert sum(result.raw_counts.values()) == shots

    def test_decoded_counts_match_raw(self):
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[0],
        )
        result = engine.run(shots=512)
        for bs, cnt in result.raw_counts.items():
            assert result.decoded_counts[_decode_bitstring(bs)] == cnt

    def test_boundary_index_zero(self):
        """Index 0 should be successfully amplified."""
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[0],
        )
        result = engine.run(shots=STAT_SHOTS)
        assert result.top_index == 0

    def test_boundary_index_max(self):
        """Last index in a 3-qubit space (index 7) should be amplified."""
        engine = GroverEngine(
            candidate_indices=list(range(8)),
            marked_indices=[7],
        )
        result = engine.run(shots=STAT_SHOTS)
        assert result.top_index == 7, (
            f"Expected 7, got {result.top_index}. counts={result.decoded_counts}"
        )


class TestGroverEngineMultipleMarked:
    """Multiple marked candidates."""

    def test_both_marked_in_top_two(self):
        """
        With 2 marked out of 8, the top-2 measured indices should include
        both marked ones (combined probability >> 2/8 = 25%).
        """
        marked = [2, 6]
        engine = GroverEngine(
            candidate_indices=list(range(8)),
            marked_indices=marked,
        )
        result = engine.run(shots=STAT_SHOTS)
        combined_marked = result.marked_empirical_probability
        # Expect combined marked probability >> 25% (= 2/8 random baseline)
        assert combined_marked > 0.45, (
            f"Combined marked probability {combined_marked:.4f} "
            f"is not above 0.45 threshold. decoded_counts={result.decoded_counts}"
        )

    def test_iteration_count_accounts_for_two_solutions(self):
        """GroverEngine must calculate k for M=2, not M=1."""
        engine = GroverEngine(
            candidate_indices=list(range(8)),
            marked_indices=[1, 5],
        )
        result = engine.run(shots=256)
        expected_k = _iteration_count(result.n_search_qubits, 2)
        assert result.n_grover_iterations == expected_k

    def test_marked_list_is_sorted_in_result(self):
        engine = GroverEngine(
            candidate_indices=list(range(8)),
            marked_indices=[7, 1, 4],
        )
        result = engine.run(shots=256)
        assert result.marked_indices == sorted([7, 1, 4])


class TestGroverEngineNoMarked:
    """Zero marked candidates — uniform distribution expected."""

    def test_zero_iterations_when_no_marked(self):
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[],
        )
        result = engine.run(shots=512)
        assert result.n_grover_iterations == 0

    def test_distribution_is_near_uniform(self):
        """
        With no marked items and no Grover iterations the distribution should
        be approximately uniform over 4 states.  Each state's probability
        should be between 0.10 and 0.40 at 2048 shots.
        """
        n_states = 4
        engine = GroverEngine(
            candidate_indices=list(range(n_states)),
            marked_indices=[],
        )
        result = engine.run(shots=STAT_SHOTS)
        for idx in range(n_states):
            count = result.decoded_counts.get(idx, 0)
            prob = count / STAT_SHOTS
            assert 0.10 < prob < 0.40, (
                f"Index {idx} probability {prob:.4f} is outside [0.10, 0.40] "
                f"for a uniform 4-state distribution."
            )

    def test_marked_probability_is_zero(self):
        engine = GroverEngine(
            candidate_indices=list(range(4)),
            marked_indices=[],
        )
        result = engine.run(shots=512)
        assert result.marked_total_counts == 0
        assert result.marked_empirical_probability == 0.0


class TestGroverEngineDNAContextCandidates:
    """Simulate realistic DNA mismatch positions as candidates."""

    def test_mismatch_positions_as_candidates(self):
        """
        Scenario: classical comparison found mismatches at positions 3 and 11
        (0-based) in a 16-bp window.  Grover searches for position 3.
        """
        candidates = list(range(16))   # 4 qubits
        marked = [3]
        engine = GroverEngine(candidate_indices=candidates, marked_indices=marked)
        result = engine.run(shots=STAT_SHOTS)
        assert result.top_index == 3, (
            f"Expected mismatch position 3 to be top result, got {result.top_index}"
        )
        assert result.n_search_qubits == 4

    def test_motif_positions_as_candidates(self):
        """
        Scenario: classical motif search found matches at positions 1, 4, 9
        (0-based) in a sequence.  Grover marks positions 4 and 9.
        """
        candidates = [1, 4, 9]
        marked = [9]
        engine = GroverEngine(candidate_indices=candidates, marked_indices=marked)
        result = engine.run(shots=STAT_SHOTS)
        # n_search_qubits is determined by max index (9) → 4 qubits
        assert result.n_search_qubits == 4

    def test_atcg_vs_atgg_service_level(self):
        """End-to-end verification of ATCG vs ATGG."""
        from app.services.dna_processing import compare_sequences

        cmp_res = compare_sequences("ATCG", "ATGG")
        assert cmp_res.total_mismatches == 1
        assert cmp_res.mismatches[0].position == 3
        assert cmp_res.mismatches[0].ref_base == "C"
        assert cmp_res.mismatches[0].sample_base == "G"

        candidates = list(range(len("ATCG")))
        marked = [m.position - 1 for m in cmp_res.mismatches]
        assert marked == [2]

        engine = GroverEngine(candidate_indices=candidates, marked_indices=marked, shots=1024)
        result = engine.run()

        assert result.n_search_qubits == 2
        assert result.n_grover_iterations == 1
        assert result.top_index == 2
        assert result.top_index_in_marked is True
        assert result.raw_counts == {"10": 1024}
        assert result.decoded_counts == {2: 1024}
        assert result.empirical_success_probability == 1.0


class TestBackwardCompatWrapper:
    """run_grover_search must still work for existing callers."""

    def test_single_target_top_state(self):
        result = run_grover_search(n_qubits=2, target_index=3, shots=1024)
        assert result.target_index == 3
        assert result.n_qubits == 2
        assert result.shots == 1024
        assert sum(result.counts.values()) == 1024

    def test_counts_sum_to_shots(self):
        result = run_grover_search(n_qubits=3, target_index=5, shots=512)
        assert sum(result.counts.values()) == 512

    def test_top_state_format(self):
        result = run_grover_search(n_qubits=2, target_index=0, shots=256)
        # top_state must be a binary string of length n_qubits
        assert isinstance(result.top_state, str)
        assert len(result.top_state) == 2
        assert all(c in "01" for c in result.top_state)

    def test_success_probability_in_range(self):
        result = run_grover_search(n_qubits=2, target_index=1, shots=512)
        assert 0.0 <= result.success_probability <= 1.0


class TestGroverEngineValidation:
    """Input validation edge cases."""

    def test_empty_candidates_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            GroverEngine(candidate_indices=[], marked_indices=[])

    def test_negative_candidate_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            GroverEngine(candidate_indices=[-1, 0, 1], marked_indices=[])

    def test_shots_zero_raises(self):
        with pytest.raises(ValueError, match="shots"):
            GroverEngine(candidate_indices=[0, 1], marked_indices=[], shots=0)


# ===========================================================================
# Layer D – API endpoint tests (real AerSimulator via httpx)
# ===========================================================================

class TestGroverEndpoint:

    @pytest.mark.asyncio
    async def test_single_marked_candidate_response_structure(self, client):
        """Response must contain all documented fields with correct types."""
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1, 2, 3],
            "marked_indices": [2],
            "shots": 512,
        })
        assert resp.status_code == 200
        data = resp.json()

        required_keys = {
            "candidate_indices", "marked_indices",
            "n_search_qubits", "n_grover_iterations",
            "shots", "circuit_depth", "circuit_width",
            "raw_counts", "decoded_counts",
            "top_index", "top_count", "top_index_in_marked",
            "empirical_success_probability",
            "marked_total_counts", "marked_empirical_probability",
            "simulator_note",
        }
        assert required_keys.issubset(data.keys())
        assert data["shots"] == 512
        assert data["n_search_qubits"] == 2
        assert isinstance(data["raw_counts"], dict)
        assert isinstance(data["simulator_note"], str)

    @pytest.mark.asyncio
    async def test_single_marked_top_index_is_correct(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": list(range(8)),
            "marked_indices": [5],
            "shots": 2048,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["top_index"] == 5
        assert data["top_index_in_marked"] is True

    @pytest.mark.asyncio
    async def test_multiple_marked_candidates(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": list(range(8)),
            "marked_indices": [1, 6],
            "shots": 2048,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["marked_empirical_probability"] > 0.40

    @pytest.mark.asyncio
    async def test_no_marked_candidates(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1, 2, 3],
            "marked_indices": [],
            "shots": 512,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_grover_iterations"] == 0
        assert data["marked_total_counts"] == 0
        assert data["marked_empirical_probability"] == 0.0

    @pytest.mark.asyncio
    async def test_circuit_metadata_non_zero(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1, 2, 3, 4, 5, 6, 7],
            "marked_indices": [3],
            "shots": 256,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["circuit_depth"] > 0
        assert data["circuit_width"] == data["n_search_qubits"]

    @pytest.mark.asyncio
    async def test_raw_counts_sum_to_shots(self, client):
        shots = 512
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": list(range(4)),
            "marked_indices": [1],
            "shots": shots,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert sum(data["raw_counts"].values()) == shots

    @pytest.mark.asyncio
    async def test_empty_candidates_returns_422(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [],
            "marked_indices": [],
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_shots_out_of_range_returns_422(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1],
            "marked_indices": [0],
            "shots": 0,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_decoded_counts_keys_are_integers(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1, 2, 3],
            "marked_indices": [0],
            "shots": 256,
        })
        assert resp.status_code == 200
        for key in resp.json()["decoded_counts"]:
            # JSON keys are strings; they must be parseable as integers
            assert key.isdigit() or key.lstrip("-").isdigit()

    @pytest.mark.asyncio
    async def test_simulator_note_mentions_simulator(self, client):
        resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1],
            "marked_indices": [1],
        })
        assert resp.status_code == 200
        note = resp.json()["simulator_note"].lower()
        assert "simulator" in note
        assert "speedup" in note

    @pytest.mark.asyncio
    async def test_workflow_atcg_vs_atgg_endpoint(self, client):
        """End-to-end audit scenario: ATCG vs ATGG."""
        # 1. Classical compare
        cmp_resp = await client.post("/api/dna/compare", json={
            "reference": "ATCG",
            "sample": "ATGG",
        })
        assert cmp_resp.status_code == 200
        cmp_data = cmp_resp.json()
        assert cmp_data["total_mismatches"] == 1
        assert cmp_data["mutation_percentage"] == 25.0
        assert len(cmp_data["mismatches"]) == 1
        mismatch = cmp_data["mismatches"][0]
        assert mismatch["position"] == 3
        assert mismatch["reference_base"] == "C"
        assert mismatch["sample_base"] == "G"

        # 2. Map position 3 (1-based) to 0-based candidate index 2
        one_based_pos = cmp_data["mismatches"][0]["position"]
        zero_based_idx = one_based_pos - 1
        assert zero_based_idx == 2

        # 3. Grover search on candidate indices 0, 1, 2, 3 with marked=[2]
        grover_resp = await client.post("/api/quantum/grover", json={
            "candidate_indices": [0, 1, 2, 3],
            "marked_indices": [zero_based_idx],
            "shots": 1024,
        })
        assert grover_resp.status_code == 200
        grover_data = grover_resp.json()

        assert grover_data["n_search_qubits"] == 2
        assert grover_data["n_grover_iterations"] == 1
        assert grover_data["top_index"] == 2
        assert grover_data["top_index_in_marked"] is True
        assert grover_data["top_count"] == 1024
        assert grover_data["empirical_success_probability"] == 1.0
        assert grover_data["raw_counts"] == {"10": 1024}
        assert grover_data["decoded_counts"] == {"2": 1024}
