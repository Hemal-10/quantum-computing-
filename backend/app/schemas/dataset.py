"""
Pydantic schemas for genomic datasets, FASTA records, and synthetic benchmarks.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


VALID_BASES = frozenset({"A", "T", "G", "C"})


class FastaRecord(BaseModel):
    """
    Representation of a single FASTA sequence record.
    """
    id: str = Field(..., description="Unique record identifier parsed from header")
    description: str = Field(default="", description="Header description following the identifier")
    sequence: str = Field(..., description="Validated DNA sequence containing only A, T, G, C")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("FASTA record identifier cannot be empty")
        return stripped

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        seq = v.strip().upper()
        if not seq:
            raise ValueError("Sequence cannot be empty")
        invalid = [b for b in seq if b not in VALID_BASES]
        if invalid:
            unique_invalid = sorted(set(invalid))
            raise ValueError(f"Sequence contains invalid nucleotide bases: {unique_invalid}. Only A, T, G, C allowed.")
        return seq


class MutationGroundTruth(BaseModel):
    """
    Exact ground-truth point mutation specification.
    Uses 1-based indexing adhering to biological standards.
    """
    position: int = Field(..., ge=1, description="1-based sequence position")
    reference_base: str = Field(..., max_length=1, description="Reference nucleotide (A, T, G, C)")
    sample_base: str = Field(..., max_length=1, description="Mutated nucleotide (A, T, G, C)")

    @field_validator("reference_base", "sample_base")
    @classmethod
    def validate_base(cls, v: str) -> str:
        base = v.strip().upper()
        if base not in VALID_BASES:
            raise ValueError(f"Invalid base '{base}'. Must be one of A, T, G, C.")
        return base

    @model_validator(mode="after")
    def check_substitution(self) -> MutationGroundTruth:
        if self.reference_base == self.sample_base:
            raise ValueError(
                f"Position {self.position}: reference_base and sample_base are identical ('{self.reference_base}'). "
                "A mutation must represent a substitution."
            )
        return self


class SyntheticDatasetConfig(BaseModel):
    """
    Parameters for generating a synthetic reference/sample sequence pair.
    """
    dataset_id: str = Field(..., description="Unique dataset identifier, e.g. 'synth_64bp_001'")
    length: int = Field(..., ge=4, le=100000, description="Total sequence length in base pairs")
    mutation_count: int = Field(..., ge=0, description="Number of deliberate single-nucleotide substitutions")
    seed: int = Field(default=42, description="Fixed random seed for deterministic reproducibility")
    gc_content: float = Field(default=0.5, ge=0.0, le=1.0, description="Target GC nucleotide ratio (0.0 to 1.0)")
    description: str = Field(default="", description="Human-readable description of this synthetic benchmark")

    @model_validator(mode="after")
    def check_mutation_count(self) -> SyntheticDatasetConfig:
        if self.mutation_count > self.length:
            raise ValueError(
                f"mutation_count ({self.mutation_count}) cannot exceed sequence length ({self.length})."
            )
        return self


class DatasetMetadata(BaseModel):
    """
    Dataset provenance, accession, and generation parameters.
    """
    dataset_id: str = Field(..., description="Dataset identifier")
    source: str = Field(..., description="Data source: 'synthetic', 'ncbi', 'clinvar'")
    accession: Optional[str] = Field(default=None, description="Official NCBI GenBank/RefSeq accession if applicable")
    genome_assembly: Optional[str] = Field(default=None, description="Reference assembly if applicable (e.g. GRCh38.p14)")
    sequence_length: int = Field(..., ge=1, description="Length of sequence in base pairs")
    generation_parameters: Optional[dict[str, Any]] = Field(default=None, description="Synthetic parameters if generated")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of generation or curation")
    notes: str = Field(default="", description="Scientific notes on provenance and intended usage")


class ExpectedResults(BaseModel):
    """
    Ground-truth expected comparison results for automated validation.
    """
    dataset_id: str = Field(..., description="Dataset identifier")
    reference_id: str = Field(..., description="Reference FASTA record identifier")
    sample_id: str = Field(..., description="Sample FASTA record identifier")
    sequence_length: int = Field(..., ge=1, description="Sequence length in base pairs")
    total_mutations: int = Field(..., ge=0, description="Total ground-truth mutations")
    mutation_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of mutated positions")
    ground_truth_mutations: list[MutationGroundTruth] = Field(
        default_factory=list,
        description="Sorted list of 1-based ground-truth mutation positions and base substitutions"
    )

    @field_validator("ground_truth_mutations")
    @classmethod
    def validate_positions_sorted(cls, v: list[MutationGroundTruth]) -> list[MutationGroundTruth]:
        positions = [m.position for m in v]
        if len(positions) != len(set(positions)):
            raise ValueError("Ground-truth mutation positions must be unique.")
        return sorted(v, key=lambda m: m.position)
