# Quantum DNA Sequence Analyzer – Genomic Datasets

This module manages offline genomic datasets, FASTA sequence parsing, synthetic benchmark generation, and metadata provenance for the Quantum DNA Sequence Analyzer.

---

## Directory Organization

```
backend/datasets/
├── raw/         # Unmodified upstream inputs (NCBI RefSeq FASTA, ClinVar VCF snippets)
├── synthetic/   # Generated synthetic FASTA sequences (reference & sample pairs)
├── processed/   # Ground-truth expected comparison results in JSON format
└── metadata/    # Dataset provenance, genome assemblies, and generation parameters
```

---

## Scientific Data Integrity & ClinVar Notice

1. **Synthetic Provenance**: Synthetic benchmarks are generated with deterministic pseudo-random seeds. They do not fabricate false NCBI GenBank accessions or false reference genome assembly tags.
2. **ClinVar VCF vs. Full Sequences**: ClinVar records in Variant Call Format (VCF) define discrete variant coordinates (`CHROM`, `POS`, `REF`, `ALT`, `CLNSIG`). **ClinVar records do not directly contain full paired reference and mutated sequences**. In order to perform sequence comparison or quantum search on ClinVar variants, variant alleles must be injected into an official reference assembly (e.g. GRCh38). This separation is strictly maintained.
3. **Decoupled Architecture**: Dataset parsing and loading are completely decoupled from the classical comparison algorithm (`app.services.dna_processing`) and the Qiskit Grover engine (`app.services.quantum_search`).

---

## Windows PowerShell Usage

### 1. Generating a Synthetic Dataset

Run the generator CLI from the `backend/` directory:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Generate a 64 bp synthetic benchmark with 3 deliberate point mutations using seed 42
python -m app.services.synthetic_generator --id "synthetic_64bp_001" --length 64 --mutations 3 --seed 42 --gc 0.5 --output-dir "datasets"
```

This command automatically generates:
- `datasets/synthetic/synthetic_64bp_001_ref.fasta`
- `datasets/synthetic/synthetic_64bp_001_sample.fasta`
- `datasets/processed/synthetic_64bp_001_expected.json`
- `datasets/metadata/synthetic_64bp_001_metadata.json`

### 2. Loading and Validating via Python

```python
from pathlib import Path
from app.services.dataset_loader import SyntheticDatasetLoader, FastaDatasetLoader

# Load and validate synthetic paired benchmark with ground truth cross-validation
loader = SyntheticDatasetLoader()
dataset = loader.load("datasets", "synthetic_64bp_001", validate_ground_truth=True)

print(f"Reference: {dataset.reference_record.id} ({len(dataset.reference_record.sequence)} bp)")
print(f"Sample:    {dataset.sample_record.id} ({len(dataset.sample_record.sequence)} bp)")
print(f"Expected:  {dataset.expected_results.total_mutations} mutations")

# Load raw NCBI reference sequence
fasta_loader = FastaDatasetLoader()
records = fasta_loader.load("datasets/raw/sample_reference.fasta")
print(f"Loaded NCBI Record: {records[0].id} ({len(records[0].sequence)} bp)")
```

---

## Running Dataset Tests

```powershell
python -m pytest tests/test_dataset_management.py -v
```
