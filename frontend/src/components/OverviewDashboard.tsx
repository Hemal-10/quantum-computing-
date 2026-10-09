import React from 'react';
import type { HealthResponse } from '../api/client';
import { GENOMIC_PRESETS, type GenomicPreset } from '../data/genomicPresets';

interface OverviewDashboardProps {
  health: HealthResponse | null;
  healthLoading: boolean;
  healthError: string | null;
  onRefreshHealth: () => void;
  onSelectPreset: (preset: GenomicPreset) => void;
  onNavigateTab: (tabId: string) => void;
}

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({
  health,
  healthLoading,
  healthError,
  onRefreshHealth,
  onSelectPreset,
  onNavigateTab,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* ── System Status & Header Banner ── */}
      <div
        className="glass-panel"
        style={{
          padding: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--color-cyan)',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
              }}
            >
              Hybrid Computational Engine
            </span>
            <span
              className={`badge ${
                healthLoading ? 'badge--loading' : health ? 'badge--ok' : 'badge--error'
              }`}
            >
              <span className={healthLoading ? 'pulse' : ''}>●</span>
              {healthLoading ? 'Connecting…' : health ? `Backend v${health.version}` : 'Disconnected'}
            </span>
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
            Quantum DNA Sequence Analysis Platform
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', marginTop: '4px' }}>
            Bridging deterministic string bioinformatics with Qiskit Grover amplitude amplification.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn-secondary"
            onClick={onRefreshHealth}
            disabled={healthLoading}
            title="Check FastAPI connection"
          >
            {healthLoading ? 'Checking…' : '↻ Ping Backend'}
          </button>
        </div>
      </div>

      {healthError && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.35)',
            color: '#fb7185',
            fontSize: '0.875rem',
          }}
        >
          <strong>Connection error:</strong> {healthError}. Ensure the FastAPI backend is running at http://127.0.0.1:8000.
        </div>
      )}

      {/* ── Pipeline Architecture Flow ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3
          style={{
            fontSize: '1rem',
            fontWeight: 700,
            color: 'var(--color-cyan)',
            marginBottom: '16px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          🔬 Computational Architecture Pipeline
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
          }}
        >
          <div
            style={{
              background: 'rgba(16, 26, 52, 0.6)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              borderRadius: '10px',
              padding: '16px',
            }}
          >
            <div style={{ color: 'var(--color-cyan)', fontWeight: 700, fontSize: '0.8125rem' }}>
              STEP 1: CLASSICAL DNA PARSER
            </div>
            <div style={{ fontWeight: 600, marginTop: '4px', fontSize: '0.9375rem' }}>
              Positional Scanning
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
              Validates A/T/G/C alphabet, scans sequence differences, and identifies exact motif occurrences with 1-based biological indexing.
            </p>
          </div>

          <div
            style={{
              background: 'rgba(16, 26, 52, 0.6)',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              borderRadius: '10px',
              padding: '16px',
            }}
          >
            <div style={{ color: 'var(--color-violet)', fontWeight: 700, fontSize: '0.8125rem' }}>
              STEP 2: CANDIDATE ENCODING
            </div>
            <div style={{ fontWeight: 600, marginTop: '4px', fontSize: '0.9375rem' }}>
              Qubit Register Allocation
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
              Allocates minimum search qubits ⌈log₂(N)⌉ and formats 0-based candidate indices into quantum computational states.
            </p>
          </div>

          <div
            style={{
              background: 'rgba(16, 26, 52, 0.6)',
              border: '1px solid rgba(34, 211, 238, 0.25)',
              borderRadius: '10px',
              padding: '16px',
            }}
          >
            <div style={{ color: 'var(--color-cyan)', fontWeight: 700, fontSize: '0.8125rem' }}>
              STEP 3: GROVER SYNTHESIS
            </div>
            <div style={{ fontWeight: 600, marginTop: '4px', fontSize: '0.9375rem' }}>
              Phase Oracle & Diffusion
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
              Phase oracle flips marked targets using multi-controlled Z gates; diffusion operator amplifies target amplitudes with optimal iterations.
            </p>
          </div>

          <div
            style={{
              background: 'rgba(16, 26, 52, 0.6)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: '10px',
              padding: '16px',
            }}
          >
            <div style={{ color: 'var(--color-emerald)', fontWeight: 700, fontSize: '0.8125rem' }}>
              STEP 4: AER SIMULATION
            </div>
            <div style={{ fontWeight: 600, marginTop: '4px', fontSize: '0.9375rem' }}>
              Measurement Decoding
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
              Executes shots on Qiskit AerSimulator, maps measured bitstrings to original candidate indices, and computes empirical probabilities.
            </p>
          </div>
        </div>
      </div>

      {/* ── Preset Genomic Scenarios ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ marginBottom: '16px' }}>
          <h3
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              color: 'var(--color-cyan)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            🧬 Benchmark Genomic Scenarios
          </h3>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '4px' }}>
            Select a verified biological test case to populate sequence comparison, motif detection, and Grover quantum search.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '14px',
          }}
        >
          {GENOMIC_PRESETS.map((preset) => (
            <div
              key={preset.id}
              style={{
                background: 'rgba(9, 14, 28, 0.7)',
                border: '1px solid rgba(56, 189, 248, 0.2)',
                borderRadius: '10px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '12px',
                transition: 'border-color 0.2s',
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--color-text-primary)' }}>
                  {preset.name}
                </div>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginTop: '4px', lineHeight: 1.4 }}>
                  {preset.description}
                </p>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    color: 'var(--color-text-secondary)',
                    marginTop: '8px',
                    wordBreak: 'break-all',
                    background: 'rgba(0,0,0,0.25)',
                    padding: '6px 8px',
                    borderRadius: '4px',
                  }}
                >
                  Ref: <span style={{ color: 'var(--color-emerald)' }}>{preset.reference}</span>
                  <br />
                  Mut: <span style={{ color: '#fb7185' }}>{preset.sample}</span>
                  {preset.motif && (
                    <>
                      <br />
                      Motif: <span style={{ color: 'var(--color-cyan)' }}>{preset.motif}</span>
                    </>
                  )}
                </div>
              </div>

              <button
                className="btn-primary"
                style={{ width: '100%', fontSize: '0.8125rem', padding: '8px' }}
                onClick={() => onSelectPreset(preset)}
              >
                Load Scenario →
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Module Navigation Cards ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '16px',
        }}
      >
        <div
          className="glass-panel"
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s' }}
          onClick={() => onNavigateTab('compare')}
        >
          <div style={{ fontSize: '1.25rem', marginBottom: '8px' }}>🧬</div>
          <h4 style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
            DNA Sequence Comparison
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
            Pairwise alignment of reference and mutant samples. Visual nucleotide diff with 1-based biological coordinate mapping.
          </p>
        </div>

        <div
          className="glass-panel"
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s' }}
          onClick={() => onNavigateTab('motif')}
        >
          <div style={{ fontSize: '1.25rem', marginBottom: '8px' }}>🔍</div>
          <h4 style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
            Genomic Motif Search
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
            Exact pattern matcher across sequences (e.g., TATA promoter, EcoRI). Overlapping match detection and visual highlighting.
          </p>
        </div>

        <div
          className="glass-panel"
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s' }}
          onClick={() => onNavigateTab('quantum')}
        >
          <div style={{ fontSize: '1.25rem', marginBottom: '8px' }}>⚛</div>
          <h4 style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
            Qiskit Grover Search Engine
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
            Synthesize phase oracles and diffusion operators. Execute quantum circuits on AerSimulator and inspect probability histograms.
          </p>
        </div>

        <div
          className="glass-panel"
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s' }}
          onClick={() => onNavigateTab('comparison')}
        >
          <div style={{ fontSize: '1.25rem', marginBottom: '8px' }}>⚖️</div>
          <h4 style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
            Classical vs Quantum Analysis
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem', marginTop: '6px' }}>
            Direct comparison of deterministic linear scan O(N) vs Grover amplitude amplification O(√N), circuit overhead, and simulation boundaries.
          </p>
        </div>
      </div>
    </div>
  );
};
