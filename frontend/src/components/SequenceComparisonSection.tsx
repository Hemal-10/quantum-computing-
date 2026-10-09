import React, { useState } from 'react';
import { apiClient, type CompareResponse } from '../api/client';
import { NucleotideViewer } from './NucleotideViewer';
import { GENOMIC_PRESETS, type GenomicPreset } from '../data/genomicPresets';

interface SequenceComparisonSectionProps {
  reference: string;
  sample: string;
  compareResult: CompareResponse | null;
  onUpdateReference: (ref: string) => void;
  onUpdateSample: (sample: string) => void;
  onCompareSuccess: (res: CompareResponse) => void;
  onSendToGrover: (mismatches: number[], seqLength: number) => void;
}

export const SequenceComparisonSection: React.FC<SequenceComparisonSectionProps> = ({
  reference,
  sample,
  compareResult,
  onUpdateReference,
  onUpdateSample,
  onCompareSuccess,
  onSendToGrover,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validate characters: only A, T, G, C allowed
  const validateChars = (seq: string) => {
    const invalid = seq.toUpperCase().split('').filter((b) => !['A', 'T', 'G', 'C'].includes(b));
    return Array.from(new Set(invalid));
  };

  const refInvalid = validateChars(reference);
  const sampleInvalid = validateChars(sample);
  const hasCharError = refInvalid.length > 0 || sampleInvalid.length > 0;
  const hasLengthMismatch = reference.length > 0 && sample.length > 0 && reference.length !== sample.length;

  const handleCompare = async () => {
    if (!reference.trim() || !sample.trim()) {
      setError('Please provide both reference and sample sequences.');
      return;
    }
    if (hasCharError) {
      setError('Sequences must contain only nucleotide bases A, T, G, and C.');
      return;
    }
    if (hasLengthMismatch) {
      setError(`Sequence lengths must match for direct positional comparison (${reference.length} vs ${sample.length}).`);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.compareDna({
        reference: reference.toUpperCase().trim(),
        sample: sample.toUpperCase().trim(),
      });
      onCompareSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (preset: GenomicPreset) => {
    onUpdateReference(preset.reference);
    onUpdateSample(preset.sample);
    setError(null);
  };

  const mismatchPositions = compareResult ? compareResult.mismatches.map((m) => m.position) : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── Sequence Inputs ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-cyan)' }}>
              Pairwise DNA Sequence Comparison
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Compare a reference sequence against a sample sequence to identify positional point mutations.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {GENOMIC_PRESETS.slice(0, 3).map((p) => (
              <button key={p.id} className="btn-secondary" onClick={() => loadPreset(p)}>
                {p.id === 'sickle-cell' ? 'Sickle Cell' : p.id === 'brca1-variant' ? 'BRCA1' : 'Control'}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Reference DNA Sequence (A, T, G, C)
              <span style={{ float: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                {reference.length} bp
              </span>
            </label>
            <input
              type="text"
              className="input-dna"
              value={reference}
              onChange={(e) => onUpdateReference(e.target.value.toUpperCase().replace(/[^A-Za-z]/g, ''))}
              placeholder="e.g. ACTCCTGAGGAGAAGT"
            />
            {refInvalid.length > 0 && (
              <span style={{ color: '#fb7185', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                Invalid characters: {refInvalid.join(', ')}
              </span>
            )}
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Sample DNA Sequence (A, T, G, C)
              <span style={{ float: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                {sample.length} bp
              </span>
            </label>
            <input
              type="text"
              className="input-dna"
              value={sample}
              onChange={(e) => onUpdateSample(e.target.value.toUpperCase().replace(/[^A-Za-z]/g, ''))}
              placeholder="e.g. ACTCCTGTGGAGAAGT"
            />
            {sampleInvalid.length > 0 && (
              <span style={{ color: '#fb7185', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                Invalid characters: {sampleInvalid.join(', ')}
              </span>
            )}
          </div>
        </div>

        {hasLengthMismatch && (
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
            ⚠️ Length mismatch: Reference is {reference.length} bp, Sample is {sample.length} bp.
            Positional pairwise comparison requires identical sequence lengths.
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

        <div style={{ marginTop: '18px', display: 'flex', gap: '12px' }}>
          <button
            className="btn-primary"
            onClick={handleCompare}
            disabled={loading || !reference || !sample || hasCharError || hasLengthMismatch}
          >
            {loading ? 'Analyzing Sequences…' : '▶ Compare Sequences (Classical)'}
          </button>
        </div>
      </div>

      {/* ── Sequence Alignment Dual Track Viewer ── */}
      {(reference || sample) && (
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Sequence Alignment & Nucleotide Mapping
            </h4>
            {compareResult && (
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8125rem',
                  color: compareResult.total_mismatches > 0 ? '#fb7185' : 'var(--color-emerald)',
                }}
              >
                {compareResult.total_mismatches} mutation(s) detected ({compareResult.mutation_percentage}%)
              </span>
            )}
          </div>

          <NucleotideViewer
            label="Reference Sequence"
            sequence={reference}
            mismatchPositions={mismatchPositions}
            highlightColor="mismatch"
          />

          <NucleotideViewer
            label="Sample Sequence (Mutant / Variant)"
            sequence={sample}
            mismatchPositions={mismatchPositions}
            highlightColor="mismatch"
          />

          {compareResult && compareResult.total_mismatches > 0 && (
            <div
              style={{
                marginTop: '8px',
                padding: '14px',
                borderRadius: '8px',
                background: 'rgba(124, 58, 237, 0.1)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.875rem' }}>
                  Prepare Grover Quantum Search on Detected Mutation Positions
                </div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem', marginTop: '2px' }}>
                  Positions: {mismatchPositions.join(', ')} (1-based) → Indices: {mismatchPositions.map((p) => p - 1).join(', ')} (0-based)
                </div>
              </div>

              <button
                className="btn-quantum"
                onClick={() => onSendToGrover(mismatchPositions, reference.length)}
              >
                ⚛ Search Mutation Positions with Grover →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
