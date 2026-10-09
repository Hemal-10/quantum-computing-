"""
Endpoint tests for POST /api/dna/compare and POST /api/dna/motif.

Covers all scenarios specified in the requirements:
  - identical sequences
  - one mismatch
  - multiple mismatches
  - invalid characters (reference, sample, sequence, motif)
  - unequal lengths
  - motif at the beginning
  - motif at the end
  - motif not found
  - overlapping motifs
  - lowercase input accepted
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE = "http://test"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        yield c


# ===========================================================================
# POST /api/dna/compare
# ===========================================================================

class TestCompareEndpoint:

    @pytest.mark.asyncio
    async def test_identical_sequences(self, client):
        """Identical sequences must yield zero mismatches and 0.0% mutation."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "ACGTACGT",
            "sample":    "ACGTACGT",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_mismatches"] == 0
        assert data["mutation_percentage"] == 0.0
        assert data["mismatches"] == []

    @pytest.mark.asyncio
    async def test_one_mismatch(self, client):
        """Single substitution at position 2 (1-based): C→T."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "ACGT",
            "sample":    "ATGT",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_mismatches"] == 1
        assert data["mutation_percentage"] == 25.0
        mismatch = data["mismatches"][0]
        assert mismatch["position"] == 2          # 1-based
        assert mismatch["ref_base"] == "C"
        assert mismatch["sample_base"] == "T"

    @pytest.mark.asyncio
    async def test_multiple_mismatches(self, client):
        """Three substitutions spread across the sequence."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "AAAACCCC",
            "sample":    "TAAACCCG",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_mismatches"] == 2
        positions = [m["position"] for m in data["mismatches"]]
        assert 1 in positions   # A→T
        assert 8 in positions   # C→G

    @pytest.mark.asyncio
    async def test_invalid_character_in_reference(self, client):
        """Invalid character in reference must return 422."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "ACGTNNN",
            "sample":    "ACGTAAA",
        })
        assert resp.status_code == 422
        body = resp.json()
        # FastAPI wraps field_validator errors inside the "detail" list
        detail_str = str(body)
        assert "invalid" in detail_str.lower() or "N" in detail_str

    @pytest.mark.asyncio
    async def test_invalid_character_in_sample(self, client):
        """Invalid character in sample must return 422."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "ACGTAAA",
            "sample":    "ACGTXYZ",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_unequal_lengths(self, client):
        """Sequences of different lengths must return 422 with a descriptive message."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "ACGT",
            "sample":    "ACGTACGT",
        })
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "same length" in detail.lower() or "reference=" in detail

    @pytest.mark.asyncio
    async def test_lowercase_input_accepted(self, client):
        """Lowercase sequences are normalised to uppercase before comparison."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "acgt",
            "sample":    "acgt",
        })
        assert resp.status_code == 200
        assert resp.json()["total_mismatches"] == 0

    @pytest.mark.asyncio
    async def test_full_mutation(self, client):
        """Every position differs → mutation_percentage == 100.0."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "AAAA",
            "sample":    "TTTT",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_mismatches"] == 4
        assert data["mutation_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_response_fields_present(self, client):
        """Response must include all documented fields."""
        resp = await client.post("/api/dna/compare", json={
            "reference": "ACGT",
            "sample":    "ACGT",
        })
        data = resp.json()
        assert set(data.keys()) >= {
            "reference_length", "sample_length",
            "total_mismatches", "mutation_percentage", "mismatches",
        }
        assert data["reference_length"] == 4
        assert data["sample_length"] == 4


# ===========================================================================
# POST /api/dna/motif
# ===========================================================================

class TestMotifEndpoint:

    @pytest.mark.asyncio
    async def test_motif_at_beginning(self, client):
        """Motif starting at position 1 (1-based) is found."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "CGTACGT",
            "motif":    "CGT",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 1 in data["positions"]

    @pytest.mark.asyncio
    async def test_motif_at_end(self, client):
        """Motif at the very end of the sequence is found."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "ACGTACGT",
            "motif":    "CGT",
        })
        assert resp.status_code == 200
        positions = resp.json()["positions"]
        seq_len = resp.json()["sequence_length"]
        motif_len = resp.json()["motif_length"]
        assert (seq_len - motif_len + 1) in positions   # last valid 1-based start

    @pytest.mark.asyncio
    async def test_motif_not_found(self, client):
        """Absent motif returns empty positions list and match_count 0."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "AAAATTTT",
            "motif":    "CGT",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_count"] == 0
        assert data["positions"] == []

    @pytest.mark.asyncio
    async def test_multiple_non_overlapping_motifs(self, client):
        """Two non-overlapping occurrences are both reported."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "ACGTACGT",
            "motif":    "CGT",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_count"] == 2
        assert data["positions"] == [2, 6]

    @pytest.mark.asyncio
    async def test_overlapping_motifs(self, client):
        """Overlapping occurrences are all reported (AAAA contains AA at 1, 2, 3)."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "AAAA",
            "motif":    "AA",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["positions"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_invalid_character_in_sequence(self, client):
        """Invalid character in sequence must return 422."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "ACGTNNN",
            "motif":    "ACG",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_character_in_motif(self, client):
        """Invalid character in motif must return 422."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "ACGTACGT",
            "motif":    "XYZ",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_lowercase_input_accepted(self, client):
        """Lowercase input is normalised; search works case-insensitively."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "acgtacgt",
            "motif":    "cgt",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_count"] == 2
        assert data["motif"] == "CGT"

    @pytest.mark.asyncio
    async def test_response_fields_present(self, client):
        """Response must contain all documented fields."""
        resp = await client.post("/api/dna/motif", json={
            "sequence": "ACGT",
            "motif":    "A",
        })
        data = resp.json()
        assert set(data.keys()) >= {
            "sequence_length", "motif", "motif_length",
            "match_count", "positions",
        }
