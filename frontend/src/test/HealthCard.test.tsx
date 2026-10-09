/**
 * @vitest-environment jsdom
 *
 * Tests for HealthCard component.
 * The real fetch is mocked so no running backend is needed.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { HealthCard } from '../components/HealthCard';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('HealthCard', () => {
  it('shows "Connecting…" while the request is pending', () => {
    // Never resolves
    mockFetch.mockReturnValue(new Promise(() => {}));
    render(<HealthCard />);
    expect(screen.getByText('Connecting…')).toBeInTheDocument();
  });

  it('renders OK status and version after a successful response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'ok',
        version: '0.1.0',
        message: 'Quantum DNA Sequence Analyzer backend is running.',
      }),
    });

    render(<HealthCard />);

    await waitFor(() => {
      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    expect(screen.getByText('ok')).toBeInTheDocument();
    expect(screen.getByText('0.1.0')).toBeInTheDocument();
    expect(
      screen.getByText('Quantum DNA Sequence Analyzer backend is running.')
    ).toBeInTheDocument();
  });

  it('shows error state when the API is unreachable', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network Error'));

    render(<HealthCard />);

    await waitFor(() => {
      expect(screen.getByText('Unreachable')).toBeInTheDocument();
    });

    expect(screen.getByText(/Network Error/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retries the request when the Retry button is clicked', async () => {
    const user = userEvent.setup();

    // First call fails
    mockFetch.mockRejectedValueOnce(new Error('Timeout'));
    // Second call succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'ok',
        version: '0.1.0',
        message: 'All good.',
      }),
    });

    render(<HealthCard />);

    await waitFor(() => screen.getByRole('button', { name: /retry/i }));
    await user.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
