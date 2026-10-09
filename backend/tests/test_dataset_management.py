"""
Unit and integration tests for the dataset management and loading module.

Covers:
- FASTA parser: valid parsing, multiline wrapping, comment lines
- Sequence validation: invalid bases, lowercase normalization, empty sequences
- Header validation: empty identifiers, duplicate identifiers, malformed headers
- Synthetic generator: reproducibility with fixed seed, exact mutation counts
- Ground-truth consistency: correct and incorrect ground-truth positions
- Loader interface: FastaDatasetLoader, SyntheticDatasetLoader, ClinVarVcfLoader
- Offline dataset verification: validates the built-in offline test fixtures
"""
import json
import pytest
from pathlib import Path

from app.schemas.dataset import (
    FastaRecord,
    MutationGroundTruth,
    SyntheticDatasetConfig,
    ExpectedResults,
)
from app.services.fasta_parser import (
    parse_fasta,
    validate_dna_sequence,
    write_fasta,
)
from app.services.synthetic_generator import (
    generate_synthetic_dataset,
    save_synthetic_dataset,
)
from app.services.dataset_loader import (
    FastaDatasetLoader,
    SyntheticDatasetLoader,
    ClinVarVcfLoader,
    get_dataset_loader,
)


# ===========================================================================
# 1. FASTA Parser & Sequence Validation Tests
# ===========================================================================

class TestFastaParser:
    """Tests for FASTA parsing, sequence validation, and error handling."""

    def test_parse_valid_single_record(self):
        fasta_text = ">seq_001 Human snippet\nACGTACGT\n"
        records = parse_fasta(fasta_text)
        assert len(records) == 1
        assert records[0].id == "seq_001"
        assert records[0].description == "Human snippet"
        assert records[0].sequence == "ACGTACGT"

    def test_parse_multiline_sequence(self):
        fasta_text = ">seq_002\nACGT\nTGCA\nAAAA\n"
        records = parse_fasta(fasta_text)
        assert len(records) == 1
        assert records[0].sequence == "ACGTTGCAAAAA"

    def test_parse_ignores_comments_and_empty_lines(self):
        fasta_text = "; comment 1\n# comment 2\n\n>seq_003\nACGT\n\nTGCA\n"
        records = parse_fasta(fasta_text)
        assert len(records) == 1
        assert records[0].sequence == "ACGTTGCA"

    def test_lowercase_normalized_to_uppercase(self):
        fasta_text = ">seq_004\nacgtacgt\n"
        records = parse_fasta(fasta_text)
        assert records[0].sequence == "ACGTACGT"

    def test_invalid_bases_raises_value_error(self):
        """Must reject invalid nucleotide characters (e.g. N, X, 1)."""
        fasta_text = ">seq_bad\nACGTNTCG\n"
        with pytest.raises(ValueError, match="invalid nucleotide characters"):
            parse_fasta(fasta_text)

    def test_empty_sequence_raises_value_error(self):
        """Must reject empty sequence data."""
        fasta_text = ">seq_empty\n\n>seq_next\nACGT\n"
        with pytest.raises(ValueError, match="empty sequence"):
            parse_fasta(fasta_text)

    def test_empty_identifier_raises_value_error(self):
        """Must reject empty header line with no identifier."""
        fasta_text = ">\nACGT\n"
        with pytest.raises(ValueError, match="empty FASTA header"):
            parse_fasta(fasta_text)

    def test_duplicate_identifiers_raises_value_error(self):
        """Must reject duplicate record identifiers."""
        fasta_text = ">seq_dup First instance\nACGT\n>seq_dup Second instance\nTGCA\n"
        with pytest.raises(ValueError, match="Duplicate FASTA identifier 'seq_dup'"):
            parse_fasta(fasta_text)

    def test_sequence_before_header_raises_value_error(self):
        fasta_text = "ACGTACGT\n>seq_005\nTGCA\n"
        with pytest.raises(ValueError, match="Malformed FASTA"):
            parse_fasta(fasta_text)

    def test_write_and_parse_roundtrip(self, tmp_path):
        record = FastaRecord(id="roundtrip_01", description="Roundtrip test", sequence="A" * 70)
        out_file = tmp_path / "test.fasta"
        write_fasta([record], out_file, line_length=50)

        parsed = parse_fasta(out_file)
        assert len(parsed) == 1
        assert parsed[0].id == "roundtrip_01"
        assert parsed[0].sequence == "A" * 70


# ===========================================================================
# 2. Synthetic Generator Tests
# ===========================================================================

class TestSyntheticGenerator:
    """Tests for synthetic dataset generator and fixed seed reproducibility."""

    def test_reproducibility_with_fixed_seed(self):
        config1 = SyntheticDatasetConfig(dataset_id="rep_01", length=32, mutation_count=2, seed=42)
        config2 = SyntheticDatasetConfig(dataset_id="rep_01", length=32, mutation_count=2, seed=42)

        ref1, smp1, exp1, _ = generate_synthetic_dataset(config1)
        ref2, smp2, exp2, _ = generate_synthetic_dataset(config2)

        assert ref1.sequence == ref2.sequence
        assert smp1.sequence == smp2.sequence
        assert exp1.ground_truth_mutations == exp2.ground_truth_mutations

    def test_different_seeds_produce_different_sequences(self):
        config1 = SyntheticDatasetConfig(dataset_id="seed_a", length=32, mutation_count=2, seed=42)
        config2 = SyntheticDatasetConfig(dataset_id="seed_b", length=32, mutation_count=2, seed=999)

        ref1, _, _, _ = generate_synthetic_dataset(config1)
        ref2, _, _, _ = generate_synthetic_dataset(config2)

        assert ref1.sequence != ref2.sequence

    def test_exact_sequence_length_and_mutation_count(self):
        config = SyntheticDatasetConfig(dataset_id="len_test", length=128, mutation_count=5, seed=123)
        ref, smp, exp, _ = generate_synthetic_dataset(config)

        assert len(ref.sequence) == 128
        assert len(smp.sequence) == 128
        assert exp.total_mutations == 5
        assert len(exp.ground_truth_mutations) == 5

        # Verify ground truth matches sequence differences
        actual_diffs = [
            (i + 1, ref.sequence[i], smp.sequence[i])
            for i in range(128)
            if ref.sequence[i] != smp.sequence[i]
        ]
        assert len(actual_diffs) == 5
        for (pos, r, s), gt in zip(actual_diffs, exp.ground_truth_mutations):
            assert pos == gt.position
            assert r == gt.reference_base
            assert s == gt.sample_base

    def test_provenance_honesty_no_fabricated_accession(self):
        config = SyntheticDatasetConfig(dataset_id="prov_test", length=32, mutation_count=1, seed=7)
        _, _, _, meta = generate_synthetic_dataset(config)

        assert meta.source == "synthetic"
        assert meta.accession is None
        assert meta.genome_assembly is None
        assert meta.generation_parameters["seed"] == 7

    def test_save_synthetic_dataset_creates_files(self, tmp_path):
        config = SyntheticDatasetConfig(dataset_id="save_test", length=40, mutation_count=2, seed=10)
        paths = save_synthetic_dataset(config, tmp_path)

        assert paths["reference_fasta"].exists()
        assert paths["sample_fasta"].exists()
        assert paths["expected_json"].exists()
        assert paths["metadata_json"].exists()


# ===========================================================================
# 3. Loader Interface & Consistency Tests
# ===========================================================================

class TestDatasetLoader:
    """Tests for dataset loaders, length mismatch, and ground-truth validation."""

    def test_synthetic_loader_valid_dataset(self, tmp_path):
        config = SyntheticDatasetConfig(dataset_id="load_valid", length=48, mutation_count=3, seed=55)
        save_synthetic_dataset(config, tmp_path)

        loader = SyntheticDatasetLoader()
        loaded = loader.load(tmp_path, "load_valid", validate_ground_truth=True)

        assert loaded.dataset_id == "load_valid"
        assert len(loaded.reference_record.sequence) == 48
        assert len(loaded.sample_record.sequence) == 48
        assert loaded.expected_results.total_mutations == 3

    def test_mismatched_sequence_lengths_raises_value_error(self, tmp_path):
        """Must reject dataset if reference and sample sequence lengths differ."""
        synth_dir = tmp_path / "synthetic"
        synth_dir.mkdir(parents=True)

        ref = FastaRecord(id="mismatch_ref", sequence="ACGTACGT")  # 8 bp
        smp = FastaRecord(id="mismatch_smp", sequence="ACGT")      # 4 bp
        write_fasta([ref], synth_dir / "mismatch_ref.fasta")
        write_fasta([smp], synth_dir / "mismatch_sample.fasta")

        loader = SyntheticDatasetLoader()
        with pytest.raises(ValueError, match="Reference length .* does not match sample length"):
            loader.load(tmp_path, "mismatch")

    def test_incorrect_ground_truth_positions_detected(self, tmp_path):
        """Must reject dataset when expected JSON ground truth doesn't match actual sequences."""
        config = SyntheticDatasetConfig(dataset_id="gt_tamper", length=30, mutation_count=2, seed=11)
        paths = save_synthetic_dataset(config, tmp_path)

        # Tamper with expected JSON: change one ground truth position
        with open(paths["expected_json"], "r", encoding="utf-8") as f:
            data = json.load(f)

        # Alter the position of the first mutation to an incorrect coordinate
        data["ground_truth_mutations"][0]["position"] = 999
        with open(paths["expected_json"], "w", encoding="utf-8") as f:
            json.dump(data, f)

        loader = SyntheticDatasetLoader()
        with pytest.raises(ValueError, match="Ground-truth mismatch"):
            loader.load(tmp_path, "gt_tamper", validate_ground_truth=True)

    def test_incorrect_ground_truth_base_detected(self, tmp_path):
        """Must reject dataset when expected base substitution differs from actual sequences."""
        config = SyntheticDatasetConfig(dataset_id="gt_base_tamper", length=30, mutation_count=1, seed=22)
        paths = save_synthetic_dataset(config, tmp_path)

        with open(paths["expected_json"], "r", encoding="utf-8") as f:
            data = json.load(f)

        # Tamper with the expected sample base (valid substitution, but different from actual sequence)
        ref_base = data["ground_truth_mutations"][0]["reference_base"]
        real_base = data["ground_truth_mutations"][0]["sample_base"]
        tampered_base = [b for b in ("A", "T", "G", "C") if b != ref_base and b != real_base][0]
        data["ground_truth_mutations"][0]["sample_base"] = tampered_base

        with open(paths["expected_json"], "w", encoding="utf-8") as f:
            json.dump(data, f)

        loader = SyntheticDatasetLoader()
        with pytest.raises(ValueError, match="Ground-truth base mismatch"):
            loader.load(tmp_path, "gt_base_tamper", validate_ground_truth=True)

    def test_clinvar_vcf_loader(self, tmp_path):
        """Test ClinVar VCF loader parses coordinates and maintains provenance integrity."""
        vcf_content = (
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "11\t5227002\trs334\tT\tA\t.\tPASS\tCLNSIG=Pathogenic\n"
            "17\t43044295\trs80357498\tC\tT\t.\tPASS\tCLNSIG=Pathogenic\n"
        )
        vcf_file = tmp_path / "test.vcf"
        vcf_file.write_text(vcf_content, encoding="utf-8")

        loader = ClinVarVcfLoader()
        variants = loader.load(vcf_file)

        assert len(variants) == 2
        assert variants[0].chromosome == "11"
        assert variants[0].position == 5227002
        assert variants[0].variant_id == "rs334"
        assert variants[0].reference_allele == "T"
        assert variants[0].alternate_allele == "A"

    def test_get_dataset_loader_factory(self):
        assert isinstance(get_dataset_loader("fasta"), FastaDatasetLoader)
        assert isinstance(get_dataset_loader("ncbi"), FastaDatasetLoader)
        assert isinstance(get_dataset_loader("synthetic"), SyntheticDatasetLoader)
        assert isinstance(get_dataset_loader("clinvar"), ClinVarVcfLoader)

        with pytest.raises(ValueError, match="Unsupported dataset loader"):
            get_dataset_loader("unsupported_format")


# ===========================================================================
# 4. Built-in Offline Datasets Verification
# ===========================================================================

class TestOfflineDatasets:
    """Ensures the built-in offline test fixtures load cleanly without network access."""

    def test_offline_synthetic_64bp_dataset(self):
        base_dir = Path(__file__).resolve().parent.parent / "datasets"
        loader = SyntheticDatasetLoader()
        loaded = loader.load(base_dir, "synthetic_64bp_001", validate_ground_truth=True)

        assert loaded.reference_record.sequence is not None
        assert len(loaded.reference_record.sequence) == 64
        assert loaded.expected_results.total_mutations == 3

    def test_offline_sample_reference_fasta(self):
        base_dir = Path(__file__).resolve().parent.parent / "datasets"
        ref_file = base_dir / "raw" / "sample_reference.fasta"
        loader = FastaDatasetLoader()
        records = loader.load(ref_file)

        assert len(records) == 1
        assert "NM_000518.5" in records[0].id
        assert len(records[0].sequence) == 494

    def test_offline_clinvar_snippet(self):
        base_dir = Path(__file__).resolve().parent.parent / "datasets"
        vcf_file = base_dir / "raw" / "sample_clinvar_snippet.vcf"
        loader = ClinVarVcfLoader()
        variants = loader.load(vcf_file)

        assert len(variants) == 2
        assert variants[0].variant_id == "rs334"
