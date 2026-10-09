import React from 'react';
import type { CompareResponse } from '../api/client';

interface MutationResultsSectionProps {
  compareResult: CompareResponse | null;
  onSendToGrover: (mismatches: number[], seqLength: number) => void;
  onNavigateToCompare: () => void;
}

export const MutationResultsSection: React.FC<MutationResultsSectionProps> = ({
  compareResult,
  onSendToGrover,
  onNavigateToCompare,
}) => {
  if (!compareResult) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🧬</div>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          No Mutation Data Available Yet
        </h3>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', maxWidth: '480px', margin: '8px auto 20px' }}>
          Run a classical sequence comparison or load a genomic preset to identify and inspect nucleotide substitutions.
        </p>
        <button className="btn-primary" onClick={onNavigateToCompare}>
          Go to Sequence Comparison →
        </button>
      </div>
    );
  }

  const { total_mismatches, reference_length, sample_length, mutation_percentage, mismatches } = compareResult;

  // Classify transition vs transversion
  const classifyMutation = (ref: string, smp: string): { label: string; desc: string } => {
    const r = ref.toUpperCase();
    const s = smp.toUpperCase();
    const isPurine = (b: string) => b === 'A' || b === 'G';

    if ((isPurine(r) && isPurine(s)) || (!isPurine(r) && !isPurine(s))) {
      return { label: 'Transition', desc: `${r} ↔ ${s} (within same ring type)` };
    }
    return { label: 'Transversion', desc: `${r} ↔ ${s} (purine ↔ pyrimidine)` };
  };

  const mismatchPositions = mismatches.map((m) => m.position);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── KPI Stat Cards ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
        }}
      >
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Sequence Length
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-cyan)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
            {reference_length} bp
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '2px' }}>
            Sample: {sample_length} bp (Identical length)
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Total Mismatches
          </div>
          <div
            style={{
              fontSize: '1.75rem',
              fontWeight: 800,
              color: total_mismatches > 0 ? '#fb7185' : 'var(--color-emerald)',
              marginTop: '4px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {total_mismatches}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '2px' }}>
            {total_mismatches === 0 ? 'Exact match' : 'Substitutions detected'}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Mutation Frequency
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-amber)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
            {mutation_percentage}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '2px' }}>
            mismatches / total bp
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Quantum Candidate Map
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--color-violet)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
            {total_mismatches} / {reference_length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '2px' }}>
            Marked states for Grover oracle
          </div>
        </div>
      </div>

      {/* ── Mismatch Breakdown Table ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Positional Mutation Directory
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              One-based biological coordinates with biochemical classification and zero-based register indexing.
            </p>
          </div>

          {total_mismatches > 0 && (
            <button
              className="btn-quantum"
              onClick={() => onSendToGrover(mismatchPositions, reference_length)}
            >
              ⚛ Launch Grover Search on {total_mismatches} Mutation(s) →
            </button>
          )}
        </div>

        {total_mismatches === 0 ? (
          <div
            style={{
              padding: '24px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              color: 'var(--color-emerald)',
              fontSize: '0.875rem',
              textAlign: 'center',
            }}
          >
            ✓ Sequences are 100% identical. No mismatches found across all {reference_length} nucleotide positions.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="dna-table">
              <thead>
                <tr>
                  <th>1-Based Pos</th>
                  <th>0-Based Reg Index</th>
                  <th>Reference Base</th>
                  <th>Sample Base</th>
                  <th>Classification</th>
                  <th>Biochemical Detail</th>
                </tr>
              </thead>
              <tbody>
                {mismatches.map((m) => {
                  const regIndex = m.position - 1;
                  const classification = classifyMutation(m.reference_base, m.sample_base);
                  return (
                    <tr key={m.position}>
                      <td style={{ fontWeight: 700, color: 'var(--color-cyan)', fontFamily: 'var(--font-mono)' }}>
                        Pos {m.position}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
                        |{regIndex}⟩
                      </td>
                      <td>
                        <span className={`nt-chip nt-${m.reference_base.toUpperCase()}`} style={{ width: 28, height: 32, fontSize: '0.8125rem' }}>
                          {m.reference_base}
                        </span>
                      </td>
                      <td>
                        <span className={`nt-chip nt-${m.sample_base.toUpperCase()} nt-mismatch`} style={{ width: 28, height: 32, fontSize: '0.8125rem' }}>
                          {m.sample_base}
                        </span>
                      </td>
                      <td>
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            background:
                              classification.label === 'Transition'
                                ? 'rgba(56, 189, 248, 0.15)'
                                : 'rgba(244, 63, 94, 0.15)',
                            color:
                              classification.label === 'Transition'
                                ? 'var(--color-cyan)'
                                : '#fb7185',
                            border: `1px solid ${
                              classification.label === 'Transition'
                                ? 'rgba(56, 189, 248, 0.3)'
                                : 'rgba(244, 63, 94, 0.3)'
                            }`,
                          }}
                        >
                          {classification.label}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem' }}>
                        {classification.desc}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Pathogenicity & Disclaimer Card ── */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 20px',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(148, 163, 184, 0.2)',
          fontSize: '0.8125rem',
          color: 'var(--color-text-muted)',
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: 'var(--color-text-primary)' }}>Important Non-Clinical Notice:</strong>{' '}
        This analysis performs deterministic string comparison to report base substitutions. It does not predict protein folding,
        variant pathogenicity, or clinical impact. Positional mismatches serve purely as predicate solutions for the quantum search experiment.
      </div>
    </div>
  );
};
