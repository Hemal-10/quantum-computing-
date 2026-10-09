import { useState, useEffect, useCallback } from 'react';
import './index.css';
import { apiClient, type HealthResponse, type CompareResponse, type GroverResponse } from './api/client';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { OverviewDashboard } from './components/OverviewDashboard';
import { SequenceComparisonSection } from './components/SequenceComparisonSection';
import { MutationResultsSection } from './components/MutationResultsSection';
import { MotifSearchSection } from './components/MotifSearchSection';
import { QuantumSearchSection } from './components/QuantumSearchSection';
import { ClassicalVsQuantumSection } from './components/ClassicalVsQuantumSection';
import { GENOMIC_PRESETS, type GenomicPreset } from './data/genomicPresets';

type TabId = 'overview' | 'compare' | 'mutations' | 'motif' | 'quantum' | 'comparison';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  // Health check state
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Shared DNA and quantum states
  const [reference, setReference] = useState(GENOMIC_PRESETS[0].reference);
  const [sample, setSample] = useState(GENOMIC_PRESETS[0].sample);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);

  const [motifSequence, setMotifSequence] = useState(GENOMIC_PRESETS[2].reference);
  const [motifPattern, setMotifPattern] = useState(GENOMIC_PRESETS[2].motif || 'TATAAA');

  const [groverCandidates, setGroverCandidates] = useState<number[]>([0, 1, 2, 3, 4, 5, 6, 7]);
  const [groverMarked, setGroverMarked] = useState<number[]>([5]);
  const [latestGroverResult, setLatestGroverResult] = useState<GroverResponse | null>(null);

  const fetchHealth = useCallback(async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const res = await apiClient.health();
      setHealth(res);
    } catch (err: unknown) {
      setHealthError(err instanceof Error ? err.message : String(err));
    } finally {
      setHealthLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  // Load a preset scenario across inputs
  const handleSelectPreset = (preset: GenomicPreset) => {
    setReference(preset.reference);
    setSample(preset.sample);
    if (preset.motif) {
      setMotifSequence(preset.reference);
      setMotifPattern(preset.motif);
    }
    setActiveTab('compare');
  };

  // Bridge from mutation/motif results to Grover Quantum Search
  const handleSendToGrover = (oneBasedPositions: number[], seqLength: number) => {
    // Candidates are all sequence positions 0..seqLength-1
    const candidates = Array.from({ length: seqLength }, (_, i) => i);
    // Convert 1-based biological positions to 0-based register indices
    const markedZeroBased = oneBasedPositions.map((p) => p - 1).filter((idx) => idx >= 0 && idx < seqLength);

    setGroverCandidates(candidates);
    setGroverMarked(markedZeroBased);
    setActiveTab('quantum');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--color-bg)',
      }}
    >
      {/* ── Top Header Navigation Bar ── */}
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          background: 'rgba(7, 11, 22, 0.85)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid rgba(56, 189, 248, 0.15)',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: '70px',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          {/* Logo & Brand */}
          <div
            style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
            onClick={() => setActiveTab('overview')}
          >
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(139, 92, 246, 0.25))',
                border: '1px solid rgba(34, 211, 238, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-cyan)',
                fontSize: '1.25rem',
                boxShadow: '0 0 15px rgba(34, 211, 238, 0.2)',
              }}
            >
              ⚛
            </div>
            <div>
              <h1 style={{ fontSize: '1.125rem', fontWeight: 800, lineHeight: 1.2 }} className="gradient-heading">
                Quantum DNA Analyzer
              </h1>
              <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                Qiskit Aer · FastAPI · React
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              overflowX: 'auto',
              maxWidth: '100%',
              padding: '4px 0',
            }}
          >
            <button
              className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`tab-btn ${activeTab === 'compare' ? 'active' : ''}`}
              onClick={() => setActiveTab('compare')}
            >
              Sequence Compare
            </button>
            <button
              className={`tab-btn ${activeTab === 'mutations' ? 'active' : ''}`}
              onClick={() => setActiveTab('mutations')}
            >
              Mutations {compareResult && compareResult.total_mismatches > 0 ? `(${compareResult.total_mismatches})` : ''}
            </button>
            <button
              className={`tab-btn ${activeTab === 'motif' ? 'active' : ''}`}
              onClick={() => setActiveTab('motif')}
            >
              Motif Search
            </button>
            <button
              className={`tab-btn ${activeTab === 'quantum' ? 'active' : ''}`}
              onClick={() => setActiveTab('quantum')}
            >
              ⚛ Grover Quantum
            </button>
            <button
              className={`tab-btn ${activeTab === 'comparison' ? 'active' : ''}`}
              onClick={() => setActiveTab('comparison')}
            >
              Classical vs Quantum
            </button>
          </nav>

          {/* Backend Connection Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              className={`badge ${
                healthLoading ? 'badge--loading' : health ? 'badge--ok' : 'badge--error'
              }`}
              style={{ fontSize: '0.7rem' }}
              title={health ? `FastAPI backend version ${health.version}` : 'Disconnected'}
            >
              <span className={healthLoading ? 'pulse' : ''}>●</span>
              {healthLoading ? 'Connecting' : health ? 'API Online' : 'Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Content Container ── */}
      <main
        style={{
          flex: 1,
          maxWidth: '1280px',
          width: '100%',
          margin: '0 auto',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        {/* Global Scientific Disclaimer Notice */}
        <DisclaimerBanner />

        {/* Tab 1: Overview Dashboard */}
        {activeTab === 'overview' && (
          <OverviewDashboard
            health={health}
            healthLoading={healthLoading}
            healthError={healthError}
            onRefreshHealth={fetchHealth}
            onSelectPreset={handleSelectPreset}
            onNavigateTab={(tab) => setActiveTab(tab as TabId)}
          />
        )}

        {/* Tab 2: DNA Sequence Comparison */}
        {activeTab === 'compare' && (
          <SequenceComparisonSection
            reference={reference}
            sample={sample}
            compareResult={compareResult}
            onUpdateReference={setReference}
            onUpdateSample={setSample}
            onCompareSuccess={(res) => setCompareResult(res)}
            onSendToGrover={handleSendToGrover}
          />
        )}

        {/* Tab 3: Mutation Results Directory */}
        {activeTab === 'mutations' && (
          <MutationResultsSection
            compareResult={compareResult}
            onSendToGrover={handleSendToGrover}
            onNavigateToCompare={() => setActiveTab('compare')}
          />
        )}

        {/* Tab 4: Motif Search */}
        {activeTab === 'motif' && (
          <MotifSearchSection
            initialSequence={motifSequence}
            initialMotif={motifPattern}
            onSendToGrover={handleSendToGrover}
          />
        )}

        {/* Tab 5: Quantum Grover Search Experiment */}
        {activeTab === 'quantum' && (
          <QuantumSearchSection
            key={`${groverCandidates.length}-${groverMarked.join(',')}`}
            initialCandidates={groverCandidates}
            initialMarked={groverMarked}
            onSimulationSuccess={(res) => setLatestGroverResult(res)}
          />
        )}

        {/* Tab 6: Classical vs Quantum Experiment Results */}
        {activeTab === 'comparison' && (
          <ClassicalVsQuantumSection
            currentSequence={reference}
            currentMismatches={compareResult ? compareResult.mismatches.map((m) => m.position) : groverMarked}
            latestGroverResult={latestGroverResult}
            onNavigateToQuantum={() => setActiveTab('quantum')}
          />
        )}
      </main>

      {/* ── Footer ── */}
      <footer
        style={{
          borderTop: '1px solid rgba(56, 189, 248, 0.1)',
          padding: '20px 24px',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'var(--color-text-dim)',
          background: 'rgba(7, 11, 22, 0.95)',
        }}
      >
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <strong>Quantum DNA Sequence Analyzer</strong> · Educational & Research Proof of Concept
          </div>
          <div style={{ fontFamily: 'var(--font-mono)' }}>
            Python FastAPI · Qiskit AerSimulator · React 19 · Recharts · TypeScript
          </div>
        </div>
      </footer>
    </div>
  );
}
