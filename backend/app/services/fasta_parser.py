"""
FASTA sequence parser and writer for the Quantum DNA Sequence Analyzer.

Supports standard FASTA formats:
- Multi-line sequence entries
- Comment lines (lines starting with ';' or '#')
- Whitespace stripping and uppercase normalization
- Strict nucleotide validation (A, T, G, C)
- Duplicate identifier detection
- File and string streaming
"""
from __future__ import annotations

from pathlib import Path
from typing import TextIO, Union

from app.schemas.dataset import FastaRecord, VALID_BASES


def validate_dna_sequence(sequence: str, record_id: str = "sequence") -> str:
    """
    Validate that a DNA sequence string is non-empty and contains only A, T, G, C.

    Returns the normalized uppercase sequence string.
    Raises ValueError on empty sequence or invalid bases.
    """
    clean_seq = "".join(sequence.split()).upper()
    if not clean_seq:
        raise ValueError(f"Record '{record_id}': DNA sequence cannot be empty.")

    invalid = sorted(set(b for b in clean_seq if b not in VALID_BASES))
    if invalid:
        raise ValueError(
            f"Record '{record_id}' contains invalid nucleotide characters: {invalid}. "
            "Only canonical DNA bases A, T, G, and C are allowed."
        )
    return clean_seq


def parse_fasta(source: Union[str, Path, TextIO]) -> list[FastaRecord]:
    """
    Parse FASTA records from a file path, string content, or text stream.

    Parameters
    ----------
    source : str | Path | TextIO
        File path, raw FASTA string, or open text file object.

    Returns
    -------
    list[FastaRecord]
        List of parsed and validated FastaRecord objects.

    Raises
    ------
    ValueError
        If duplicate identifiers are found, sequences are empty,
        invalid nucleotide characters are present, or format is malformed.
    FileNotFoundError
        If a provided file path does not exist.
    """
    lines: list[str] = []

    if isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"FASTA file not found: {source}")
        with open(source, "r", encoding="utf-8") as f:
            lines = f.readlines()
    elif isinstance(source, str):
        # Could be a path string or direct FASTA content
        potential_path = Path(source)
        if "\n" not in source and potential_path.exists() and potential_path.is_file():
            with open(potential_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        else:
            lines = source.splitlines()
    elif hasattr(source, "readlines"):
        lines = source.readlines()
    else:
        raise TypeError(f"Unsupported FASTA source type: {type(source)}")

    records: list[FastaRecord] = []
    seen_ids: set[str] = set()

    current_id: str | None = None
    current_desc: str = ""
    current_seq_parts: list[str] = []

    def commit_record():
        nonlocal current_id, current_desc, current_seq_parts
        if current_id is None:
            return

        raw_sequence = "".join(current_seq_parts)
        if not raw_sequence:
            raise ValueError(f"Record '{current_id}' has an empty sequence.")

        validated_seq = validate_dna_sequence(raw_sequence, record_id=current_id)

        record = FastaRecord(
            id=current_id,
            description=current_desc,
            sequence=validated_seq,
        )
        records.append(record)

        current_id = None
        current_desc = ""
        current_seq_parts = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue

        if line.startswith(">"):
            commit_record()

            header = line[1:].strip()
            if not header:
                raise ValueError("Encountered empty FASTA header line ('>' with no identifier).")

            parts = header.split(maxsplit=1)
            record_id = parts[0]
            description = parts[1] if len(parts) > 1 else ""

            if record_id in seen_ids:
                raise ValueError(
                    f"Duplicate FASTA identifier '{record_id}' found. Identifiers within a dataset must be unique."
                )

            seen_ids.add(record_id)
            current_id = record_id
            current_desc = description
        else:
            if current_id is None:
                raise ValueError(f"Malformed FASTA: sequence data found before header line: '{line[:30]}...'")
            current_seq_parts.append(line)

    commit_record()

    if not records:
        raise ValueError("FASTA source contains no valid sequence records.")

    return records


def write_fasta(records: list[FastaRecord], output_path: Union[str, Path], line_length: int = 60) -> None:
    """
    Write FASTA records to a file, wrapping sequences at line_length characters.

    Parameters
    ----------
    records : list[FastaRecord]
        List of records to write.
    output_path : str | Path
        Destination file path.
    line_length : int, default 60
        Line wrap width for the sequence text.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            header = f">{record.id}"
            if record.description:
                header += f" {record.description}"
            f.write(f"{header}\n")

            seq = record.sequence
            for i in range(0, len(seq), line_length):
                f.write(f"{seq[i:i + line_length]}\n")
