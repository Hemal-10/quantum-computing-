"""
Extensible Dataset Loader interface for the Quantum DNA Sequence Analyzer.

Supports:
1. FASTA dataset loading (synthetic, NCBI reference genomes).
2. Synthetic benchmark verification (paired reference/sample + ground-truth validation).
3. ClinVar VCF variant specification loader interface.

Scientific Integrity Notice
----------------------------
ClinVar records in VCF format specify variant coordinates (CHROM, POS, REF, ALT,
clinical significance). They do NOT directly contain complete paired genomic
sequences. To perform positional comparison or quantum search on ClinVar variants,
the variant records must be mapped and injected into a corresponding reference
assembly (e.g. GRCh38 / GRCh37). This loader enforces this distinction and
strictly avoids fabricating full-length paired sequences from raw VCF files.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from app.schemas.dataset import (
    DatasetMetadata,
    ExpectedResults,
    FastaRecord,
    MutationGroundTruth,
    VALID_BASES,
)
from app.services.fasta_parser import parse_fasta


@dataclass
class LoadedPairDataset:
    """
    A loaded paired sequence dataset ready for analysis.
    """
    dataset_id: str
    reference_record: FastaRecord
    sample_record: FastaRecord
    expected_results: Optional[ExpectedResults] = None
    metadata: Optional[DatasetMetadata] = None


@dataclass
class ClinVarVariantRecord:
    """
    Representation of a single ClinVar variant from a VCF file.
    Does NOT contain a full-length genomic sequence.
    """
    chromosome: str
    position: int              # 1-based coordinate in reference assembly
    variant_id: str            # ClinVar Variation ID or rsID
    reference_allele: str      # REF base(s)
    alternate_allele: str      # ALT base(s)
    filter_status: str = "PASS"
    info: dict[str, Any] = None  # Clinical significance, review status, etc.


class BaseDatasetLoader(ABC):
    """
    Abstract base loader interface for genomic datasets.
    """

    @abstractmethod
    def load(self, source: Path | str, **kwargs) -> Any:
        """Load and parse dataset from the given source path or identifier."""
        pass


class FastaDatasetLoader(BaseDatasetLoader):
    """
    Loader for standard FASTA sequence files (e.g. NCBI RefSeq or local FASTA).
    """

    def load(self, source: Path | str, **kwargs) -> list[FastaRecord]:
        """
        Parse all validated FASTA records from a file path or FASTA string.
        """
        return parse_fasta(source)


class SyntheticDatasetLoader(BaseDatasetLoader):
    """
    Loader and validator for synthetic paired benchmark datasets.
    Validates that:
    1. Reference and sample sequences exist and are valid.
    2. Sequence lengths match.
    3. Stored ground-truth mutations accurately reflect the actual differences between sequences.
    """

    def load(
        self,
        base_dir: Path | str,
        dataset_id: str,
        validate_ground_truth: bool = True,
    ) -> LoadedPairDataset:
        """
        Load synthetic reference FASTA, sample FASTA, expected JSON, and metadata JSON.

        Parameters
        ----------
        base_dir : Path | str
            Base dataset directory containing 'synthetic', 'processed', and 'metadata'.
        dataset_id : str
            Dataset identifier, e.g. 'synthetic_benchmark_001'.
        validate_ground_truth : bool, default True
            If True, rigorously cross-validates ground-truth positions against the sequences.

        Returns
        -------
        LoadedPairDataset
        """
        base = Path(base_dir)
        ref_path = base / "synthetic" / f"{dataset_id}_ref.fasta"
        sample_path = base / "synthetic" / f"{dataset_id}_sample.fasta"
        expected_path = base / "processed" / f"{dataset_id}_expected.json"
        metadata_path = base / "metadata" / f"{dataset_id}_metadata.json"

        if not ref_path.exists():
            raise FileNotFoundError(f"Reference FASTA not found: {ref_path}")
        if not sample_path.exists():
            raise FileNotFoundError(f"Sample FASTA not found: {sample_path}")

        ref_records = parse_fasta(ref_path)
        sample_records = parse_fasta(sample_path)

        if len(ref_records) != 1:
            raise ValueError(f"Expected exactly 1 reference record, found {len(ref_records)}")
        if len(sample_records) != 1:
            raise ValueError(f"Expected exactly 1 sample record, found {len(sample_records)}")

        ref_rec = ref_records[0]
        sample_rec = sample_records[0]

        # Check sequence lengths
        if len(ref_rec.sequence) != len(sample_rec.sequence):
            raise ValueError(
                f"Dataset '{dataset_id}': Reference length ({len(ref_rec.sequence)}) does not "
                f"match sample length ({len(sample_rec.sequence)})."
            )

        expected: Optional[ExpectedResults] = None
        if expected_path.exists():
            with open(expected_path, "r", encoding="utf-8") as f:
                expected = ExpectedResults.model_validate(json.load(f))

        metadata: Optional[DatasetMetadata] = None
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = DatasetMetadata.model_validate(json.load(f))

        # Cross-validate ground truth against actual sequences
        if validate_ground_truth and expected is not None:
            self._validate_ground_truth_consistency(ref_rec.sequence, sample_rec.sequence, expected)

        return LoadedPairDataset(
            dataset_id=dataset_id,
            reference_record=ref_rec,
            sample_record=sample_rec,
            expected_results=expected,
            metadata=metadata,
        )

    @staticmethod
    def _validate_ground_truth_consistency(
        ref_seq: str,
        sample_seq: str,
        expected: ExpectedResults,
    ) -> None:
        """
        Verify that expected ground truth positions and bases perfectly match actual sequences.
        """
        # 1. Compute actual positional differences
        actual_diffs: list[MutationGroundTruth] = []
        for i, (r, s) in enumerate(zip(ref_seq, sample_seq)):
            if r != s:
                actual_diffs.append(
                    MutationGroundTruth(position=i + 1, reference_base=r, sample_base=s)
                )

        if len(actual_diffs) != expected.total_mutations:
            raise ValueError(
                f"Ground-truth count mismatch: expected JSON specifies {expected.total_mutations} "
                f"mutations, but actual sequence diff found {len(actual_diffs)} mismatches."
            )

        expected_map = {m.position: m for m in expected.ground_truth_mutations}
        for actual in actual_diffs:
            if actual.position not in expected_map:
                raise ValueError(
                    f"Ground-truth mismatch: Position {actual.position} differs in sequences ({actual.reference_base}→{actual.sample_base}), "
                    "but is missing from expected results."
                )
            exp = expected_map[actual.position]
            if exp.reference_base != actual.reference_base or exp.sample_base != actual.sample_base:
                raise ValueError(
                    f"Ground-truth base mismatch at position {actual.position}: expected {exp.reference_base}→{exp.sample_base}, "
                    f"actual sequences show {actual.reference_base}→{actual.sample_base}."
                )


class ClinVarVcfLoader(BaseDatasetLoader):
    """
    Loader for ClinVar variant call format (VCF) files.

    IMPORTANT SCIENTIFIC DISTINCTION:
    A ClinVar VCF file defines point variants, insertions, deletions, and clinical
    significance ratings at discrete genomic positions. It does NOT contain a full
    paired sequence. To produce paired sequences for comparison or quantum search,
    these variants must subsequently be projected onto an external reference assembly FASTA.
    """

    def load(self, source: Path | str, **kwargs) -> list[ClinVarVariantRecord]:
        """
        Parse variant records from a ClinVar VCF file without fabricating sequence context.
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"VCF file not found: {path}")

        records: list[ClinVarVariantRecord] = []

        with open(path, "r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                cols = line.split("\t")
                if len(cols) < 5:
                    raise ValueError(
                        f"Malformed VCF line {line_no}: expected at least 5 tab-delimited columns (CHROM, POS, ID, REF, ALT)."
                    )

                chrom = cols[0]
                try:
                    pos = int(cols[1])
                    if pos < 1:
                        raise ValueError
                except ValueError:
                    raise ValueError(f"Invalid VCF coordinate on line {line_no}: '{cols[1]}' must be a positive integer.")

                var_id = cols[2]
                ref_allele = cols[3].upper()
                alt_allele = cols[4].upper()
                filter_status = cols[6] if len(cols) > 6 else "PASS"

                # Validate bases for SNVs
                invalid_ref = [b for b in ref_allele if b not in VALID_BASES]
                if invalid_ref:
                    raise ValueError(f"Line {line_no}: invalid reference allele '{ref_allele}'.")

                record = ClinVarVariantRecord(
                    chromosome=chrom,
                    position=pos,
                    variant_id=var_id,
                    reference_allele=ref_allele,
                    alternate_allele=alt_allele,
                    filter_status=filter_status,
                )
                records.append(record)

        return records


def get_dataset_loader(source_type: str) -> BaseDatasetLoader:
    """
    Factory function for dataset loaders.
    """
    source_lower = source_type.lower().strip()
    if source_lower in ("fasta", "ncbi"):
        return FastaDatasetLoader()
    elif source_lower == "synthetic":
        return SyntheticDatasetLoader()
    elif source_lower in ("vcf", "clinvar"):
        return ClinVarVcfLoader()
    else:
        raise ValueError(
            f"Unsupported dataset loader type: '{source_type}'. "
            "Supported types: 'fasta', 'synthetic', 'clinvar'."
        )
