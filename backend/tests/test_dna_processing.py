"""Tests for classical DNA processing utilities."""
import pytest

from app.services.dna_processing import (
    compare_sequences,
    compute_stats,
    encode_sequence_for_grover,
    find_motif_positions,
    find_mutations,
    reverse_complement,
    search_motif,
    validate_sequence,
)


class TestValidateSequence:
    def test_valid_sequence(self):
        ok, inv = validate_sequence("ACGTACGT")
        assert ok is True
        assert inv == []

    def test_invalid_chars(self):
        ok, inv = validate_sequence("ACGTXNZ")
        assert ok is False
        assert "X" in inv
        assert "N" in inv
        assert "Z" in inv

    def test_lowercase_accepted(self):
        ok, _ = validate_sequence("acgt")
        assert ok is True


class TestComputeStats:
    def test_gc_content(self):
        # GGCC → GC=4, AT=0 → 100%
        stats = compute_stats("GGCC")
        assert stats.gc_content == 1.0
        assert stats.base_counts["G"] == 2
        assert stats.base_counts["C"] == 2

    def test_mixed_gc(self):
        stats = compute_stats("ATAT")
        assert stats.gc_content == 0.0

    def test_length(self):
        stats = compute_stats("ACGT")
        assert stats.length == 4


class TestReverseComplement:
    def test_simple(self):
        assert reverse_complement("ATCG") == "CGAT"

    def test_palindrome(self):
        assert reverse_complement("AATT") == "AATT"


class TestFindMotifPositions:
    def test_single_match(self):
        assert find_motif_positions("ACGTACGT", "CGT") == [1, 5]

    def test_no_match(self):
        assert find_motif_positions("AAAA", "CGT") == []

    def test_overlapping(self):
        # AAA contains AA at 0 and 1
        assert find_motif_positions("AAA", "AA") == [0, 1]


class TestFindMutations:
    def test_single_substitution(self):
        muts = find_mutations("ACGT", "ATGT")
        assert len(muts) == 1
        assert muts[0] == {"position": 1, "ref": "C", "alt": "T"}

    def test_no_mutations(self):
        assert find_mutations("ACGT", "ACGT") == []

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            find_mutations("ACG", "ACGT")


class TestEncodeForGrover:
    def test_basic_encoding(self):
        result = encode_sequence_for_grover("ACGT", 2)
        assert result["n_qubits"] == 2  # ceil(log2(4)) = 2
        assert result["target_index"] == 2
        assert result["database_size"] == 4

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            encode_sequence_for_grover("ACGT", 10)

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            encode_sequence_for_grover("A", 0)


# ===========================================================================
# Service-layer tests for compare_sequences
# ===========================================================================

class TestCompareSequences:

    def test_identical_returns_no_mismatches(self):
        result = compare_sequences("ACGT", "ACGT")
        assert result.total_mismatches == 0
        assert result.mutation_percentage == 0.0
        assert result.mismatches == []

    def test_one_mismatch_position_and_bases(self):
        """C at position 2 becomes T → 1-based position 2."""
        result = compare_sequences("ACGT", "ATGT")
        assert result.total_mismatches == 1
        assert result.mutation_percentage == 25.0
        m = result.mismatches[0]
        assert m.position == 2
        assert m.ref_base == "C"
        assert m.sample_base == "T"

    def test_multiple_mismatches(self):
        result = compare_sequences("AAAACCCC", "TAAACCCG")
        assert result.total_mismatches == 2
        positions = [m.position for m in result.mismatches]
        assert 1 in positions
        assert 8 in positions

    def test_full_mismatch(self):
        result = compare_sequences("AAAA", "TTTT")
        assert result.total_mismatches == 4
        assert result.mutation_percentage == 100.0

    def test_unequal_length_raises_clear_message(self):
        with pytest.raises(ValueError) as exc_info:
            compare_sequences("ACGT", "ACGTACGT")
        msg = str(exc_info.value)
        assert "same length" in msg.lower() or "reference=" in msg

    def test_invalid_char_in_reference_raises(self):
        with pytest.raises(ValueError, match="Reference"):
            compare_sequences("ACGTNN", "ACGTAA")

    def test_invalid_char_in_sample_raises(self):
        with pytest.raises(ValueError, match="Sample"):
            compare_sequences("ACGTAA", "ACGTXZ")

    def test_lowercase_normalised(self):
        result = compare_sequences("acgt", "acgt")
        assert result.total_mismatches == 0

    def test_mutation_percentage_precision(self):
        """1 mismatch in 3 bp → 33.3333%."""
        result = compare_sequences("ACG", "ATG")
        assert result.mutation_percentage == round(1 / 3 * 100, 4)

    def test_result_lengths_populated(self):
        result = compare_sequences("ACGT", "ACGT")
        assert result.reference_length == 4
        assert result.sample_length == 4


# ===========================================================================
# Service-layer tests for search_motif
# ===========================================================================

class TestSearchMotif:

    def test_motif_at_beginning(self):
        result = search_motif("CGTAAA", "CGT")
        assert 1 in result.positions

    def test_motif_at_end(self):
        result = search_motif("AAACGT", "CGT")
        assert result.positions == [4]

    def test_motif_not_present(self):
        result = search_motif("AAAATTTT", "CGT")
        assert result.match_count == 0
        assert result.positions == []

    def test_two_non_overlapping_occurrences(self):
        result = search_motif("ACGTACGT", "CGT")
        assert result.positions == [2, 6]
        assert result.match_count == 2

    def test_overlapping_occurrences(self):
        result = search_motif("AAAA", "AA")
        assert result.positions == [1, 2, 3]

    def test_invalid_char_in_sequence_raises(self):
        with pytest.raises(ValueError, match="Sequence"):
            search_motif("ACGTNNN", "ACG")

    def test_invalid_char_in_motif_raises(self):
        with pytest.raises(ValueError, match="Motif"):
            search_motif("ACGTACGT", "XYZ")

    def test_lowercase_normalised(self):
        result = search_motif("acgtacgt", "cgt")
        assert result.match_count == 2
        assert result.motif == "CGT"

    def test_result_metadata(self):
        result = search_motif("ACGT", "CG")
        assert result.sequence_length == 4
        assert result.motif_length == 2

    def test_motif_longer_than_sequence_raises(self):
        with pytest.raises(ValueError, match="exceeds"):
            search_motif("AC", "ACGT")
