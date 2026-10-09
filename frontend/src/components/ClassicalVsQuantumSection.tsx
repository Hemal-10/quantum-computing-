import React, { useState } from 'react';
import { apiClient, type CompareResponse, type GroverResponse } from '../api/client';

interface ClassicalVsQuantumSectionProps {
  currentSequence?: string;
  currentMismatches?: number[];
  latestGroverResult?: GroverResponse | null;
  onNavigateToQuantum: () => void;
}

export const ClassicalVsQuantumSection: React.FC<ClassicalVsQuantumSectionProps> = ({
  currentSequence = 'ACTCCTGAGGAGAAGT',
  currentMismatches = [5],
  latestGroverResult,
  onNavigateToQuantum,
}) => {
  const [runningBenchmark, setRunningBenchmark] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState<{
    classicalTimeMs: number;
    quantumTimeMs: number;
    classicalMatches: number;
    quantumTopMatch: number | null;
    quantumSuccessRate: number;
    nQubits: number;
    iterations: number;
    depth: number;
  } | null>(null);

  const runComparativeBenchmark = async () => {
    setRunningBenchmark(true);
    try {
      const candidates = Array.from({ length: currentSequence.length }, (_, i) => i);
      const marked = currentMismatches.map((p) => (p > 0 && p <= currentSequence.length ? p - 1 : p));

      // 1. Benchmark Classical Search
      const t0 = performance.now();
      const classicalRes: CompareResponse = await apiClient.compareDna({
        reference: currentSequence,
        sample: currentSequence.slice(0, 5) + (currentSequence[5] === 'A' ? 'T' : 'A') + currentSequence.slice(6),
      });
      const t1 = performance.now();
      const classicalTime = Math.max(0.1, Number((t1 - t0).toFixed(2)));

      // 2. Benchmark Quantum Simulation
      const t2 = performance.now();
      const quantumRes: GroverResponse = await apiClient.runGrover({
        candidate_indices: candidates,
        marked_indices: marked.length > 0 ? marked : [5],
        shots: 1024,
      });
      const t3 = performance.now();
      const quantumTime = Math.max(0.1, Number((t3 - t2).toFixed(2)));

      setBenchmarkResult({
        classicalTimeMs: classicalTime,
        quantumTimeMs: quantumTime,
        classicalMatches: classicalRes.total_mismatches,
        quantumTopMatch: quantumRes.top_index,
        quantumSuccessRate: Number((quantumRes.marked_empirical_probability * 100).toFixed(1)),
        nQubits: quantumRes.n_search_qubits,
        iterations: quantumRes.n_grover_iterations,
        depth: quantumRes.circuit_depth,
      });
    } catch {
      // In case benchmark fails, reset
    } finally {
      setRunningBenchmark(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* ── Section Header ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-cyan)' }}>
          Classical Bioinformatics vs. Quantum Grover Search
        </h3>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', marginTop: '4px' }}>
          An empirical comparison of deterministic classical sequence scanning against Grover amplitude amplification on Qiskit AerSimulator.
        </p>

        <div style={{ marginTop: '16px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            className="btn-quantum"
            onClick={runComparativeBenchmark}
            disabled={runningBenchmark}
          >
            {runningBenchmark ? 'Executing Benchmark Suite…' : '⚡ Run Live Comparative Benchmark'}
          </button>
          {latestGroverResult && (
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
              Active Grover run: {latestGroverResult.shots} shots | Top: |{latestGroverResult.top_index}⟩ ({(latestGroverResult.marked_empirical_probability * 100).toFixed(1)}% target success)
            </span>
          )}
        </div>
      </div>

      {/* ── Live Benchmark Output ── */}
      {benchmarkResult && (
        <div
          className="glass-panel"
          style={{
            padding: '24px',
            border: '1px solid rgba(34, 211, 238, 0.4)',
            boxShadow: '0 0 20px rgba(34, 211, 238, 0.1)',
          }}
        >
          <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '16px' }}>
            ⚡ Live Empirical Benchmark Results ({currentSequence.length} bp Search Space)
          </h4>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            <div style={{ background: 'rgba(16, 26, 52, 0.6)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-cyan)', textTransform: 'uppercase' }}>
                Classical Search (CPU)
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {benchmarkResult.classicalTimeMs} ms
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '4px' }}>
                Determinism: 100% exact match | Linear scan: {currentSequence.length} operations
              </div>
            </div>

            <div style={{ background: 'rgba(16, 26, 52, 0.6)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-violet)', textTransform: 'uppercase' }}>
                Quantum Simulation (Aer)
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {benchmarkResult.quantumTimeMs} ms
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '4px' }}>
                Success Rate: {benchmarkResult.quantumSuccessRate}% | Iterations: {benchmarkResult.iterations} | Qubits: {benchmarkResult.nQubits}
              </div>
            </div>

            <div style={{ background: 'rgba(16, 26, 52, 0.6)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-emerald)', textTransform: 'uppercase' }}>
                Quantum Circuit Depth
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
                {benchmarkResult.depth} gates
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '4px' }}>
                Transpiled gate layer depth for {benchmarkResult.nQubits} qubits
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Side-by-Side Comparison Table ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '16px' }}>
          Architectural & Complexity Comparison
        </h4>

        <div style={{ overflowX: 'auto' }}>
          <table className="dna-table">
            <thead>
              <tr>
                <th style={{ width: '22%' }}>Dimension</th>
                <th style={{ width: '39%', color: 'var(--color-cyan)' }}>Classical Sequence Analysis</th>
                <th style={{ width: '39%', color: 'var(--color-violet)' }}>Qiskit Grover Search Engine</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 600 }}>Algorithmic Complexity</td>
                <td>
                  <strong style={{ color: 'var(--color-cyan)', fontFamily: 'var(--font-mono)' }}>O(N)</strong> query complexity. Linear sequential or hash-based scanning over <em>N</em> positions.
                </td>
                <td>
                  <strong style={{ color: 'var(--color-violet)', fontFamily: 'var(--font-mono)' }}>O(√N)</strong> quadratic speedup. Amplitude amplification rotates state vector in √N iterations.
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Execution Mode</td>
                <td>
                  <strong>Deterministic:</strong> Guarantees 100% exact positional discovery every run. Zero sampling variance.
                </td>
                <td>
                  <strong>Probabilistic:</strong> Measured via projective measurement shots. Yields empirical distribution peaking on target state.
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Hardware Infrastructure</td>
                <td>
                  Standard classical CPU / SIMD / GPU memory pipelines. Nanosecond-level instruction latency.
                </td>
                <td>
                  Requires coherent quantum processor with fault-tolerant gates. Currently simulated via <strong>AerSimulator</strong> state-vectors.
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Register Allocation</td>
                <td>
                  <em>N</em> bytes buffer allocation in system memory.
                </td>
                <td>
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>⌈log₂(N)⌉</strong> search qubits addressing 2ⁿ Hilbert space superpositions.
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Noise & Decoherence</td>
                <td>
                  Impervious to thermal decoherence. Deterministic bit flips are negligible (ECC protected).
                </td>
                <td>
                  Simulated as ideal unitary gates in Aer. Real NISQ quantum devices suffer gate infidelities and decoherence.
                </td>
              </tr>
              <tr>
                <td style={{ fontWeight: 600 }}>Biological Applicability</td>
                <td>
                  Industry standard for clinical NGS pipelines, BLAST, and variant call formats (VCF).
                </td>
                <td>
                  Theoretical model and exploratory prototype for future quantum bioinformatics and unstructured search.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Scientific Discussion & Physical Limitations ── */}
      <div
        className="glass-panel"
        style={{
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Scientific Discussion: Where Does Quantum Advantage Truly Reside?
        </h4>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', lineHeight: 1.6 }}>
          In classical computing, searching a structured database or string can often achieve <em>O(log N)</em> or <em>O(1)</em> through indexing structures (e.g. B-trees, FM-indexes, hash tables). Grover&rsquo;s Algorithm proves an optimal bound of <strong>O(√N)</strong> for <em>unstructured</em> search problems where no indexing heuristic exists.
        </p>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', lineHeight: 1.6 }}>
          In our implementation, constructing the quantum oracle uses the known mutation indices classically to synthesize phase-inversion gates for AerSimulator. On physical quantum computers, Grover search requires a quantum oracle that computes the target predicate directly in superposition (e.g. quantum pattern recognition or boolean function evaluation).
        </p>
        <div style={{ marginTop: '8px' }}>
          <button className="btn-secondary" onClick={onNavigateToQuantum}>
            ← Adjust Parameters in Quantum Search Engine
          </button>
        </div>
      </div>
    </div>
  );
};
