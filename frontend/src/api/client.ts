/**
 * Typed API client for communicating with the FastAPI backend.
 * Covers health, classical DNA comparison, motif search, and Qiskit Grover search.
 */

export interface HealthResponse {
  status: string;
  version: string;
  message: string;
}

export interface MismatchItem {
  position: number; // 1-based index
  reference_base: string;
  sample_base: string;
}

export interface CompareRequest {
  reference: string;
  sample: string;
}

export interface CompareResponse {
  reference_length: number;
  sample_length: number;
  total_mismatches: number;
  mutation_percentage: number;
  mismatches: MismatchItem[];
}

export interface MotifRequest {
  sequence: string;
  motif: string;
}

export interface MotifResponse {
  sequence_length: number;
  motif: string;
  motif_length: number;
  match_count: number;
  positions: number[]; // 1-based indices
}

export interface GroverRequest {
  candidate_indices: number[];
  marked_indices: number[];
  shots?: number;
}

export interface GroverResponse {
  candidate_indices: number[];
  marked_indices: number[];
  n_search_qubits: number;
  n_grover_iterations: number;
  shots: number;
  circuit_depth: number;
  circuit_width: number;
  raw_counts: Record<string, number>;
  decoded_counts: Record<string, number>;
  top_index: number | null;
  top_count: number;
  top_index_in_marked: boolean;
  empirical_success_probability: number;
  marked_total_counts: number;
  marked_empirical_probability: number;
  simulator_note: string;
}

const envUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
const BASE_URL = envUrl
  ? (envUrl.endsWith('/api') ? envUrl : `${envUrl.replace(/\/+$/, '')}/api`)
  : '/api';


async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      // Read the body as text ONCE to avoid "body stream already read" error
      const text = await res.text();
      if (text) {
        try {
          const data = JSON.parse(text);
          if (typeof data.detail === 'string') {
            errorDetail = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorDetail = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(', ');
          } else {
            errorDetail = JSON.stringify(data.detail || data);
          }
        } catch {
          // Not JSON — use raw text
          errorDetail = text;
        }
      }
    } catch {
      // Network-level failure — keep default HTTP status message
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  /** GET /api/health */
  health: (): Promise<HealthResponse> => apiFetch<HealthResponse>('/health'),

  /** POST /api/dna/compare */
  compareDna: (data: CompareRequest): Promise<CompareResponse> =>
    apiFetch<CompareResponse>('/dna/compare', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** POST /api/dna/motif */
  searchMotif: (data: MotifRequest): Promise<MotifResponse> =>
    apiFetch<MotifResponse>('/dna/motif', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** POST /api/quantum/grover */
  runGrover: (data: GroverRequest): Promise<GroverResponse> =>
    apiFetch<GroverResponse>('/quantum/grover', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
