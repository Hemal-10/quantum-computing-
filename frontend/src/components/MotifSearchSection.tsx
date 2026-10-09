import React, { useState } from 'react';
import { apiClient, type MotifResponse } from '../api/client';
import { NucleotideViewer } from './NucleotideViewer';

interface MotifSearchSectionProps {
  initialSequence?: string;
  initialMotif?: string;
  onSendToGrover: (matchPositions: number[], seqLength: number) => void;
}

export const MotifSearchSection: React.FC<MotifSearchSectionProps> = ({
  initialSequence = 'CTATAAAGGGCTATAAACCC',
  initialMotif = 'TATAAA',
  onSendToGrover,
}) => {
  const [sequence, setSequence] = useState(initialSequence);
  const [motif, setMotif] = useState(initialMotif);
  const [result, setResult] = useState<MotifResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateChars = (seq: string) => {
    return Array.from(new Set(seq.toUpperCase().split('').filter((b) => !['A', 'T', 'G', 'C'].includes(b))));
  };

  const seqInvalid = validateChars(sequence);
  const motifInvalid = validateChars(motif);
  const hasCharError = seqInvalid.length > 0 || motifInvalid.length > 0;
  const isMotifTooLong = motif.length > sequence.length && sequence.length > 0;

  const handleSearch = async () => {
    if (!sequence.trim() || !motif.trim()) {
      setError('Please provide both sequence and motif.');
      return;
    }
    if (hasCharError) {
      setError('Both sequence and motif must contain only nucleotide bases A, T, G, and C.');
      return;
    }
    if (isMotifTooLong) {
      setError(`Motif length (${motif.length}) cannot exceed sequence length (${sequence.length}).`);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.searchMotif({
        sequence: sequence.toUpperCase().trim(),
        motif: motif.toUpperCase().trim(),
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const setPreset = (s: string, m: string) => {
    setSequence(s);
    setMotif(m);
    setError(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── Motif Search Form ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-cyan)' }}>
              Genomic Motif & Regulatory Sequence Search
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Locate exact genomic sub-sequences including overlapping promoter elements, restriction sites, and binding motifs.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              className="btn-secondary"
              onClick={() => setPreset('CTATAAAGGGCTATAAACCC', 'TATAAA')}
            >
              TATA Box (2x)
            </button>
            <button
              className="btn-secondary"
              onClick={() => setPreset('GCATGAATTCCGGATCGAATTC', 'GAATTC')}
            >
              EcoRI Sites
            </button>
            <button
              className="btn-secondary"
              onClick={() => setPreset('ATGCGATGCAAATGC', 'ATG')}
            >
              Start Codon ATG
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Target DNA Sequence
              <span style={{ float: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                {sequence.length} bp
              </span>
            </label>
            <input
              type="text"
              className="input-dna"
              value={sequence}
              onChange={(e) => setSequence(e.target.value.toUpperCase().replace(/[^A-Za-z]/g, ''))}
              placeholder="e.g. CTATAAAGGGCTATAAACCC"
            />
            {seqInvalid.length > 0 && (
              <span style={{ color: '#fb7185', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                Invalid characters in sequence: {seqInvalid.join(', ')}
              </span>
            )}
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Motif Pattern to Locate
              <span style={{ float: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                {motif.length} bp
              </span>
            </label>
            <input
              type="text"
              className="input-dna"
              value={motif}
              onChange={(e) => setMotif(e.target.value.toUpperCase().replace(/[^A-Za-z]/g, ''))}
              placeholder="e.g. TATAAA"
            />
            {motifInvalid.length > 0 && (
              <span style={{ color: '#fb7185', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                Invalid characters in motif: {motifInvalid.join(', ')}
              </span>
            )}
          </div>
        </div>

        {isMotifTooLong && (
          <div
            style={{
              marginTop: '14px',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              color: '#fbbf24',
              fontSize: '0.8125rem',
            }}
          >
            ⚠️ Motif length ({motif.length} bp) cannot exceed sequence length ({sequence.length} bp).
          </div>
        )}

        {error && (
          <div
            style={{
              marginTop: '14px',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(244, 63, 94, 0.12)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#fb7185',
              fontSize: '0.8125rem',
            }}
          >
            ❌ {error}
          </div>
        )}

        <div style={{ marginTop: '18px' }}>
          <button
            className="btn-primary"
            onClick={handleSearch}
            disabled={loading || !sequence || !motif || hasCharError || isMotifTooLong}
          >
            {loading ? 'Searching Motifs…' : '🔍 Find Motif Occurrences (Classical)'}
          </button>
        </div>
      </div>

      {/* ── Motif Results Track ── */}
      {result && (
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                Motif Search Output: &ldquo;{result.motif}&rdquo;
              </h4>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                {result.match_count === 0
                  ? 'No occurrences found in sequence'
                  : `Found ${result.match_count} match(es) at 1-based position(s): ${result.positions.join(', ')}`}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8125rem',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  background: result.match_count > 0 ? 'rgba(34, 211, 238, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                  color: result.match_count > 0 ? 'var(--color-cyan)' : 'var(--color-text-muted)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                }}
              >
                Match Count: {result.match_count}
              </span>
            </div>
          </div>

          <NucleotideViewer
            label="Sequence with Highlighted Motif Tracks"
            sequence={sequence}
            motifPositions={result.positions}
            motifLength={result.motif_length}
            highlightColor="motif"
          />

          {result.match_count > 0 && (
            <div
              style={{
                marginTop: '8px',
                padding: '16px',
                borderRadius: '8px',
                background: 'rgba(124, 58, 237, 0.12)',
                border: '1px solid rgba(139, 92, 246, 0.35)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.875rem' }}>
                  Execute Grover's Algorithm on Motif Positions
                </div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>
                  Candidates: 0..{sequence.length - 1} | Marked Targets: {result.positions.map((p) => p - 1).join(', ')} (0-based)
                </div>
              </div>

              <button
                className="btn-quantum"
                onClick={() => onSendToGrover(result.positions, sequence.length)}
              >
                ⚛ Search Motif Positions in Grover Circuit →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
