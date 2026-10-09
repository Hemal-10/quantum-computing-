"""
Synthetic DNA dataset generator for controlled testing and benchmarking.

Produces:
1. Reference sequences with configurable length and GC content.
2. Sample sequences with deliberately introduced single-nucleotide substitutions.
3. Exact ground-truth mutation positions (1-based biological indexing).
4. Full dataset metadata and expected JSON outputs.

Uses fixed random seeds for deterministic reproducibility.
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from app.schemas.dataset import (
    DatasetMetadata,
    ExpectedResults,
    FastaRecord,
    MutationGroundTruth,
    SyntheticDatasetConfig,
    VALID_BASES,
)
from app.services.fasta_parser import write_fasta


def generate_synthetic_dataset(
    config: SyntheticDatasetConfig,
) -> Tuple[FastaRecord, FastaRecord, ExpectedResults, DatasetMetadata]:
    """
    Generate a synthetic reference/sample sequence pair with exact ground truth.

    Parameters
    ----------
    config : SyntheticDatasetConfig
        Specification including sequence length, mutation count, seed, and GC content.

    Returns
    -------
    tuple of (reference_record, sample_record, expected_results, metadata)
    """
    rng = random.Random(config.seed)

    # 1. Generate reference sequence according to GC content
    # P(G) = P(C) = gc / 2,  P(A) = P(T) = (1 - gc) / 2
    gc_half = config.gc_content / 2.0
    at_half = (1.0 - config.gc_content) / 2.0
    bases = ["G", "C", "A", "T"]
    weights = [gc_half, gc_half, at_half, at_half]

    ref_bases = rng.choices(bases, weights=weights, k=config.length)
    sample_bases = list(ref_bases)

    # 2. Select distinct mutation positions (0-based)
    mutation_indices = sorted(rng.sample(range(config.length), config.mutation_count))

    ground_truth: list[MutationGroundTruth] = []

    for idx in mutation_indices:
        ref_base = ref_bases[idx]
        # Choose a different base uniformly from the other 3
        alt_options = sorted(VALID_BASES - {ref_base})
        alt_base = rng.choice(alt_options)

        sample_bases[idx] = alt_base

        # 1-based biological position
        gt = MutationGroundTruth(
            position=idx + 1,
            reference_base=ref_base,
            sample_base=alt_base,
        )
        ground_truth.append(gt)

    ref_seq = "".join(ref_bases)
    sample_seq = "".join(sample_bases)

    ref_record = FastaRecord(
        id=f"{config.dataset_id}_ref",
        description=f"Synthetic reference sequence ({config.length} bp, seed={config.seed})",
        sequence=ref_seq,
    )

    sample_record = FastaRecord(
        id=f"{config.dataset_id}_sample",
        description=f"Synthetic sample sequence with {config.mutation_count} substitutions",
        sequence=sample_seq,
    )

    mutation_pct = round((config.mutation_count / config.length) * 100.0, 4) if config.length > 0 else 0.0

    expected = ExpectedResults(
        dataset_id=config.dataset_id,
        reference_id=ref_record.id,
        sample_id=sample_record.id,
        sequence_length=config.length,
        total_mutations=config.mutation_count,
        mutation_percentage=mutation_pct,
        ground_truth_mutations=ground_truth,
    )

    metadata = DatasetMetadata(
        dataset_id=config.dataset_id,
        source="synthetic",
        accession=None,  # Do not fabricate real accessions
        genome_assembly=None,  # Synthetic sequences do not belong to real assemblies
        sequence_length=config.length,
        generation_parameters={
            "seed": config.seed,
            "target_gc_content": config.gc_content,
            "mutation_count": config.mutation_count,
            "length": config.length,
        },
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=(
            f"Synthetically generated benchmark dataset. Controlled point mutations "
            f"introduced at {len(ground_truth)} positions for reproducibility testing. "
            f"{config.description}"
        ),
    )

    return ref_record, sample_record, expected, metadata


def save_synthetic_dataset(
    config: SyntheticDatasetConfig,
    base_dir: Path,
) -> dict[str, Path]:
    """
    Generate and save synthetic dataset artifacts into standard directories:
    - base_dir/synthetic/ : FASTA files for reference and sample
    - base_dir/processed/ : Expected results JSON
    - base_dir/metadata/  : Dataset metadata JSON

    Returns
    -------
    dict[str, Path]
        Paths of all generated files.
    """
    base_dir = Path(base_dir)
    synthetic_dir = base_dir / "synthetic"
    processed_dir = base_dir / "processed"
    metadata_dir = base_dir / "metadata"

    synthetic_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    ref_rec, sample_rec, expected, metadata = generate_synthetic_dataset(config)

    ref_fasta_path = synthetic_dir / f"{config.dataset_id}_ref.fasta"
    sample_fasta_path = synthetic_dir / f"{config.dataset_id}_sample.fasta"
    expected_path = processed_dir / f"{config.dataset_id}_expected.json"
    metadata_path = metadata_dir / f"{config.dataset_id}_metadata.json"

    # Write FASTAs
    write_fasta([ref_rec], ref_fasta_path)
    write_fasta([sample_rec], sample_fasta_path)

    # Write Expected JSON
    with open(expected_path, "w", encoding="utf-8") as f:
        json.dump(expected.model_dump(), f, indent=2)

    # Write Metadata JSON
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    return {
        "reference_fasta": ref_fasta_path,
        "sample_fasta": sample_fasta_path,
        "expected_json": expected_path,
        "metadata_json": metadata_path,
    }


def main():
    """CLI entry point for generating synthetic datasets on Windows PowerShell."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic DNA benchmark dataset for Quantum DNA Sequence Analyzer."
    )
    parser.add_argument("--id", default="synthetic_benchmark_001", help="Dataset identifier")
    parser.add_argument("--length", type=int, default=64, help="Sequence length in base pairs")
    parser.add_argument("--mutations", type=int, default=3, help="Number of mutations to introduce")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--gc", type=float, default=0.5, help="Target GC content ratio (0.0 - 1.0)")
    parser.add_argument("--output-dir", default="datasets", help="Base dataset directory path")

    args = parser.parse_args()

    config = SyntheticDatasetConfig(
        dataset_id=args.id,
        length=args.length,
        mutation_count=args.mutations,
        seed=args.seed,
        gc_content=args.gc,
    )

    created = save_synthetic_dataset(config, Path(args.output_dir))
    print(f"Generated synthetic dataset '{config.dataset_id}':")
    for k, v in created.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
