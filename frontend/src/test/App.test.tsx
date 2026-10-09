/**
 * @vitest-environment jsdom
 *
 * Full integration tests for App and its specialized sections:
 * 1. Overview dashboard & preset selection
 * 2. DNA sequence comparison with 1-based indexing
 * 3. Mutation results table and biochemical classification
 * 4. Motif search with sequence track highlighting
 * 5. Quantum Grover search experiment with circuit metadata & Recharts
 * 6. Classical vs Quantum comparison panel
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('Quantum DNA Sequence Analyzer App Integration', () => {
  const mockHealthResponse = {
    status: 'ok',
    version: '0.1.0',
    message: 'Backend operational',
  };

  it('renders application header, navigation tabs, and disclaimer notice', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthResponse,
    });

    render(<App />);

    expect(screen.getByText('Quantum DNA Analyzer')).toBeInTheDocument();
    expect(screen.getByText(/Scientific Simulation Notice/i)).toBeInTheDocument();

    // Check all 6 tabs
    expect(screen.getByRole('button', { name: /^Overview$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Sequence Compare$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Mutations/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Motif Search$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Grover Quantum/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Classical vs Quantum$/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('API Online')).toBeInTheDocument();
    });
  });

  it('switches between tabs when navigation buttons are clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthResponse,
    });

    const user = userEvent.setup();
    render(<App />);

    // Click "Sequence Compare"
    await user.click(screen.getByRole('button', { name: /^Sequence Compare$/i }));
    expect(screen.getByText(/Pairwise DNA Sequence Comparison/i)).toBeInTheDocument();

    // Click "Motif Search"
    await user.click(screen.getByRole('button', { name: /^Motif Search$/i }));
    expect(screen.getByText(/Genomic Motif & Regulatory Sequence Search/i)).toBeInTheDocument();

    // Click "Grover Quantum"
    await user.click(screen.getByRole('button', { name: /Grover Quantum/i }));
    expect(screen.getByText(/Qiskit Grover Search Engine Simulation/i)).toBeInTheDocument();

    // Click "Classical vs Quantum"
    await user.click(screen.getByRole('button', { name: /^Classical vs Quantum$/i }));
    expect(screen.getByText(/Classical Bioinformatics vs. Quantum Grover Search/i)).toBeInTheDocument();
  });

  it('performs DNA sequence comparison and displays 1-based mutation positions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthResponse,
    });

    const user = userEvent.setup();
    render(<App />);

    // Go to Sequence Compare tab
    await user.click(screen.getByRole('button', { name: /^Sequence Compare$/i }));

    // Mock compare API response (Sickle Cell mutation at position 8: A -> T)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        reference_length: 16,
        sample_length: 16,
        total_mismatches: 1,
        mutation_percentage: 6.25,
        mismatches: [
          {
            position: 8,
            reference_base: 'A',
            sample_base: 'T',
          },
        ],
      }),
    });

    const compareBtn = screen.getByRole('button', { name: /Compare Sequences \(Classical\)/i });
    await user.click(compareBtn);

    await waitFor(() => {
      expect(screen.getByText(/1 mutation\(s\) detected/i)).toBeInTheDocument();
    });

    // Check that button to bridge to Grover is present
    expect(
      screen.getByRole('button', { name: /Search Mutation Positions with Grover/i })
    ).toBeInTheDocument();
  });

  it('executes Motif Search and displays matching positions', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthResponse,
    });

    const user = userEvent.setup();
    render(<App />);

    // Go to Motif Search tab
    await user.click(screen.getByRole('button', { name: /^Motif Search$/i }));

    // Mock motif API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        sequence_length: 20,
        motif: 'TATAAA',
        motif_length: 6,
        match_count: 2,
        positions: [2, 12],
      }),
    });

    const searchBtn = screen.getByRole('button', { name: /Find Motif Occurrences \(Classical\)/i });
    await user.click(searchBtn);

    await waitFor(() => {
      expect(screen.getByText(/Found 2 match\(es\) at 1-based position\(s\): 2, 12/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Match Count: 2/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Search Motif Positions in Grover Circuit/i })).toBeInTheDocument();
  });

  it('runs Qiskit Grover Search and displays circuit metadata and simulation output', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealthResponse,
    });

    const user = userEvent.setup();
    render(<App />);

    // Go to Grover Quantum tab
    await user.click(screen.getByRole('button', { name: /Grover Quantum/i }));

    // Mock Grover quantum response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        candidate_indices: [0, 1, 2, 3, 4, 5, 6, 7],
        marked_indices: [5],
        n_search_qubits: 3,
        n_grover_iterations: 2,
        shots: 1024,
        circuit_depth: 27,
        circuit_width: 3,
        raw_counts: { '101': 970, '000': 8 },
        decoded_counts: { '5': 970, '0': 8 },
        top_index: 5,
        top_count: 970,
        top_index_in_marked: true,
        empirical_success_probability: 0.9472,
        marked_total_counts: 970,
        marked_empirical_probability: 0.9472,
        simulator_note: 'Results are from AerSimulator (local state-vector simulator).',
      }),
    });

    const execBtn = screen.getByRole('button', { name: /Execute Grover on AerSimulator/i });
    await user.click(execBtn);

    await waitFor(() => {
      expect(screen.getByText('3 Qubits')).toBeInTheDocument();
      expect(screen.getByText('94.7%')).toBeInTheDocument();
    });

    expect(screen.getByText(/Results are from AerSimulator/i)).toBeInTheDocument();
    expect(screen.getByText(/Gate layers transpiled/i)).toBeInTheDocument();
  });
});
