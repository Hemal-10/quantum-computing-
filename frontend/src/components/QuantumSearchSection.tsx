import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { apiClient, type GroverResponse } from '../api/client';

interface QuantumSearchSectionProps {
  initialCandidates?: number[];
  initialMarked?: number[];
  onSimulationSuccess?: (res: GroverResponse) => void;
}

export const QuantumSearchSection: React.FC<QuantumSearchSectionProps> = ({
  initialCandidates = [0, 1, 2, 3, 4, 5, 6, 7],
  initialMarked = [5],
  onSimulationSuccess,
}) => {
  const [candidateStr, setCandidateStr] = useState(initialCandidates.join(', '));
  const [markedStr, setMarkedStr] = useState(initialMarked.join(', '));
  const [shots, setShots] = useState(1024);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GroverResponse | null>(null);
  const [viewMode, setViewMode] = useState<'probability' | 'counts'>('probability');
  const [labelMode, setLabelMode] = useState<'index' | 'bitstring'>('index');

  // Parse comma-separated inputs safely
  const parseIndices = (str: string): number[] => {
    return str
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0 && !isNaN(Number(s)))
      .map(Number);
  };

  const parsedCandidates = parseIndices(candidateStr);
  const parsedMarked = parseIndices(markedStr);

  // Pre-calculated stats for UI preview
  const previewQubits = parsedCandidates.length > 0 ? Math.max(1, Math.ceil(Math.log2(parsedCandidates.length))) : 1;
  const previewSpace = Math.pow(2, previewQubits);
  const previewUniformProb = (100 / previewSpace).toFixed(2);

  const handleRunGrover = async () => {
    if (parsedCandidates.length === 0) {
      setError('Please provide at least one candidate position index.');
      return;
    }
    const invalidMarked = parsedMarked.filter((m) => !parsedCandidates.includes(m));
    if (invalidMarked.length > 0) {
      setError(`Marked indices [${invalidMarked.join(', ')}] must be present in candidate positions.`);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.runGrover({
        candidate_indices: parsedCandidates,
        marked_indices: parsedMarked,
        shots,
      });
      setResult(res);
      if (onSimulationSuccess) {
        onSimulationSuccess(res);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (cands: number[], marks: number[]) => {
    setCandidateStr(cands.join(', '));
    setMarkedStr(marks.join(', '));
    setError(null);
  };

  // Prepare chart data from simulation result
  const chartData = React.useMemo(() => {
    if (!result) return [];

    const markedSet = new Set(result.marked_indices);
    const nQubits = result.n_search_qubits;

    // Use decoded counts as primary source
    const entries = Object.entries(result.decoded_counts).map(([key, count]) => {
      const idx = Number(key);
      const isMarked = markedSet.has(idx);
      // Format bitstring (Qiskit big-endian representation for display)
      const bitstring = idx >= 0 ? idx.toString(2).padStart(nQubits, '0') : 'N/A';
      const probPercent = Number(((count / result.shots) * 100).toFixed(2));

      return {
        index: idx,
        bitstring,
        label: labelMode === 'index' ? `State |${idx}⟩` : `|${bitstring}⟩`,
        count,
        probability: probPercent,
        isMarked,
      };
    });

    // Sort numerically by index
    return entries.sort((a, b) => a.index - b.index);
  }, [result, labelMode]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* ── Grover Configuration Panel ── */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-cyan)' }}>
              Qiskit Grover Search Engine Simulation
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Encode DNA candidate coordinates into a quantum register, synthesize the phase oracle & diffusion operator, and execute on AerSimulator.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              className="btn-secondary"
              onClick={() => loadPreset([0, 1, 2, 3, 4, 5, 6, 7], [5])}
            >
              Single Target (N=8, M=1)
            </button>
            <button
              className="btn-secondary"
              onClick={() => loadPreset([0, 1, 2, 3, 4, 5, 6, 7], [2, 6])}
            >
              Two Targets (N=8, M=2)
            </button>
            <button
              className="btn-secondary"
              onClick={() => loadPreset(Array.from({ length: 16 }, (_, i) => i), [3, 11])}
            >
              16 Candidates (N=16)
            </button>
            <button
              className="btn-secondary"
              onClick={() => loadPreset([0, 1, 2, 3], [])}
            >
              Zero Targets (Uniform)
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Candidate Position Indices (0-Based)
            </label>
            <input
              type="text"
              className="input-dna"
              value={candidateStr}
              onChange={(e) => setCandidateStr(e.target.value)}
              placeholder="e.g. 0, 1, 2, 3, 4, 5, 6, 7"
            />
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '4px' }}>
              {parsedCandidates.length} candidate(s) → {previewQubits} search qubit(s) required (Hilbert space = {previewSpace})
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              Marked Solution Indices (Oracle Target Predicate)
            </label>
            <input
              type="text"
              className="input-dna"
              value={markedStr}
              onChange={(e) => setMarkedStr(e.target.value)}
              placeholder="e.g. 5 or 2, 6"
            />
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-dim)', marginTop: '4px' }}>
              {parsedMarked.length} marked target(s) | Baseline uniform prob: ~{previewUniformProb}%
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                AerSimulator Measurement Shots
              </label>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--color-cyan)' }}>
                {shots} shots
              </span>
            </div>
            <input
              type="range"
              min="64"
              max="4096"
              step="64"
              value={shots}
              onChange={(e) => setShots(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--color-cyan)', marginTop: '8px' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--color-text-dim)', marginTop: '2px' }}>
              <span>64</span>
              <span>1024</span>
              <span>4096</span>
            </div>
          </div>
        </div>

        {error && (
          <div
            style={{
              marginTop: '16px',
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

        <div style={{ marginTop: '20px', display: 'flex', gap: '12px' }}>
          <button
            className="btn-quantum"
            onClick={handleRunGrover}
            disabled={loading || parsedCandidates.length === 0}
          >
            {loading ? 'Synthesizing Circuit & Simulating…' : '⚛ Execute Grover on AerSimulator'}
          </button>
        </div>
      </div>

      {/* ── Results & Circuit Metadata ── */}
      {result && (
        <>
          {/* Circuit Metadata Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '14px',
            }}
          >
            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Search Qubits
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-cyan)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                {result.n_search_qubits} Qubits
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-dim)' }}>
                Register width: 2^{result.n_search_qubits} = {Math.pow(2, result.n_search_qubits)} states
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Grover Iterations
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-violet)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                {result.n_grover_iterations}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-dim)' }}>
                k ≈ (π/4θ - 0.5) rotations
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Circuit Depth
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--color-amber)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                {result.circuit_depth}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-dim)' }}>
                Gate layers transpiled
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Empirical Success
              </div>
              <div
                style={{
                  fontSize: '1.5rem',
                  fontWeight: 800,
                  color: result.top_index_in_marked ? 'var(--color-emerald)' : '#fb7185',
                  fontFamily: 'var(--font-mono)',
                  marginTop: '2px',
                }}
              >
                {(result.marked_empirical_probability * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-dim)' }}>
                Top: |{result.top_index}⟩ ({result.top_count} shots)
              </div>
            </div>
          </div>

          {/* Recharts Quantum Histogram Panel */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
                marginBottom: '20px',
              }}
            >
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  AerSimulator Measurement Distribution
                </h4>
                <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                  Empirical probability distribution across all {chartData.length} measured register states ({result.shots} shots).
                </p>
              </div>

              {/* View & Label Controls */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', background: 'rgba(9, 14, 28, 0.8)', padding: '3px', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <button
                    className={`btn-secondary ${viewMode === 'probability' ? 'active' : ''}`}
                    style={{
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      background: viewMode === 'probability' ? 'rgba(34, 211, 238, 0.2)' : 'transparent',
                      color: viewMode === 'probability' ? 'var(--color-cyan)' : 'var(--color-text-muted)',
                      border: 'none',
                    }}
                    onClick={() => setViewMode('probability')}
                  >
                    Probability (%)
                  </button>
                  <button
                    className={`btn-secondary ${viewMode === 'counts' ? 'active' : ''}`}
                    style={{
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      background: viewMode === 'counts' ? 'rgba(34, 211, 238, 0.2)' : 'transparent',
                      color: viewMode === 'counts' ? 'var(--color-cyan)' : 'var(--color-text-muted)',
                      border: 'none',
                    }}
                    onClick={() => setViewMode('counts')}
                  >
                    Raw Shots
                  </button>
                </div>

                <div style={{ display: 'flex', background: 'rgba(9, 14, 28, 0.8)', padding: '3px', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                  <button
                    style={{
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      background: labelMode === 'index' ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                      color: labelMode === 'index' ? 'var(--color-violet)' : 'var(--color-text-muted)',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                    onClick={() => setLabelMode('index')}
                  >
                    Decoded |x⟩
                  </button>
                  <button
                    style={{
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      background: labelMode === 'bitstring' ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                      color: labelMode === 'bitstring' ? 'var(--color-violet)' : 'var(--color-text-muted)',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                    onClick={() => setLabelMode('bitstring')}
                  >
                    Bitstrings
                  </button>
                </div>
              </div>
            </div>

            {/* Recharts Bar Chart */}
            <div style={{ width: '100%', height: 320, minHeight: 320 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={300}>
                <BarChart data={chartData} margin={{ top: 15, right: 20, left: 0, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.06)" vertical={false} />
                  <XAxis
                    dataKey="label"
                    stroke="var(--color-text-muted)"
                    fontSize={11}
                    tickLine={false}
                    interval={0}
                    angle={-25}
                    textAnchor="end"
                  />
                  <YAxis
                    stroke="var(--color-text-muted)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    unit={viewMode === 'probability' ? '%' : ''}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a1020',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '0.8125rem',
                      fontFamily: 'var(--font-mono)',
                    }}
                    formatter={(val) =>
                      viewMode === 'probability'
                        ? [`${val}%`, 'Empirical Probability']
                        : [`${val} shots`, 'Measurement Counts']
                    }
                  />
                  {viewMode === 'probability' && (
                    <ReferenceLine
                      y={Number(previewUniformProb)}
                      stroke="#94a3b8"
                      strokeDasharray="4 4"
                      label={{
                        value: `Uniform (${previewUniformProb}%)`,
                        fill: '#94a3b8',
                        fontSize: 10,
                        position: 'insideTopRight',
                      }}
                    />
                  )}
                  <Bar dataKey={viewMode === 'probability' ? 'probability' : 'count'} radius={[4, 4, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell
                        key={`cell-${entry.index}`}
                        fill={
                          entry.isMarked
                            ? 'url(#markedGradient)'
                            : 'rgba(51, 65, 85, 0.7)'
                        }
                        stroke={entry.isMarked ? '#22d3ee' : 'transparent'}
                        strokeWidth={entry.isMarked ? 1.5 : 0}
                      />
                    ))}
                  </Bar>
                  <defs>
                    <linearGradient id="markedGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.95} />
                      <stop offset="100%" stopColor="#7c3aed" stopOpacity={0.75} />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Legend & Legend Notes */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '24px',
                marginTop: '16px',
                fontSize: '0.8125rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '14px',
                    height: '14px',
                    borderRadius: '3px',
                    background: 'linear-gradient(135deg, #22d3ee, #7c3aed)',
                    border: '1px solid #22d3ee',
                  }}
                />
                <span>
                  Marked Target State ({result.marked_indices.map((m) => `|${m}⟩`).join(', ') || 'None'})
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '14px',
                    height: '14px',
                    borderRadius: '3px',
                    background: 'rgba(51, 65, 85, 0.7)',
                  }}
                />
                <span>Unmarked Non-Solution State</span>
              </div>
            </div>
          </div>

          {/* Simulator Note Alert */}
          <div
            style={{
              padding: '14px 18px',
              borderRadius: '8px',
              background: 'rgba(15, 23, 42, 0.7)',
              border: '1px solid rgba(148, 163, 184, 0.25)',
              fontSize: '0.8125rem',
              color: 'var(--color-text-muted)',
              lineHeight: 1.5,
            }}
          >
            <strong style={{ color: 'var(--color-text-primary)' }}>Qiskit Backend Note:</strong> {result.simulator_note}
          </div>
        </>
      )}
    </div>
  );
};
