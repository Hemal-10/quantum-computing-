export interface GenomicPreset {
  id: string;
  name: string;
  description: string;
  reference: string;
  sample: string;
  motif?: string;
}

export const GENOMIC_PRESETS: GenomicPreset[] = [
  {
    id: 'atcg-transversion',
    name: 'ATCG vs ATGG (C→G Point Mutation)',
    description: 'Minimal 4 bp test sequence: single C→G transversion at position 3 (0-based index 2), 2 qubits, 1 Grover iteration.',
    reference: 'ATCG',
    sample:    'ATGG',
    motif: 'TCG',
  },
  {
    id: 'sickle-cell',
    name: 'Sickle Cell Anemia (HBB gene snippet)',
    description: 'Classic A→T transversion at codon 6 of beta-globin causing Glu6Val substitution.',
    reference: 'ACTCCTGAGGAGAAGT',
    sample:    'ACTCCTGTGGAGAAGT',
    motif: 'CCTG',
  },
  {
    id: 'brca1-variant',
    name: 'BRCA1 Gene Fragment',
    description: 'Human BRCA1 exon fragment containing 2 localized nucleotide substitutions.',
    reference: 'GACAAATGCCAGTGTT',
    sample:    'GACAAATGGCAGTGCT',
    motif: 'AATG',
  },
  {
    id: 'tata-box',
    name: 'TATA-Box Promoter Sequence',
    description: 'Eukaryotic core promoter region with duplicate TATAAA regulatory motifs.',
    reference: 'CTATAAAGGGCTATAAACCC',
    sample:    'CTATAAAGGGCTATAAACCC',
    motif: 'TATAAA',
  },
  {
    id: 'ecori-restriction',
    name: 'EcoRI Restriction Enzyme Site',
    description: 'Hexameric restriction site GAATTC palindrome embedded in cloning vector.',
    reference: 'GCATGAATTCCGGATC',
    sample:    'GCATGAATTCCGGATC',
    motif: 'GAATTC',
  },
  {
    id: 'negative-control',
    name: 'Identical Control (Zero Mismatches)',
    description: 'Perfect alignment baseline control with zero mutations.',
    reference: 'AGCTAGCTAGCTAGCT',
    sample:    'AGCTAGCTAGCTAGCT',
    motif: 'AGCT',
  },
];
