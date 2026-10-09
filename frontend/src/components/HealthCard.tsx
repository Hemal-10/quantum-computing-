import { useEffect, useState } from 'react';
import { apiClient, type HealthResponse } from '../api/client';
import './HealthCard.css';

type Status = 'idle' | 'loading' | 'ok' | 'error';

/**
 * HealthCard
 * Calls GET /api/health on mount and displays the result in a glassmorphic card.
 */
export function HealthCard() {
  const [status, setStatus] = useState<Status>('idle');
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setStatus('loading');
    setError(null);
    setData(null);
    try {
      const result = await apiClient.health();
      setData(result);
      setStatus('ok');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStatus('error');
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const badgeClass =
    status === 'ok'
      ? 'badge badge--ok'
      : status === 'error'
        ? 'badge badge--error'
        : 'badge badge--loading';

  const badgeLabel =
    status === 'loading' ? 'Connecting…' : status === 'ok' ? 'Online' : 'Unreachable';

  return (
    <div className="health-card glass fade-in" role="status" aria-live="polite">
      {/* Header */}
      <div className="health-card__header">
        <div className="health-card__icon" aria-hidden="true">🧬</div>
        <div>
          <div className="health-card__title">API Health Check</div>
          <div className="health-card__subtitle">GET /api/health</div>
        </div>
        <span className={badgeClass} style={{ marginLeft: 'auto' }}>
          {status === 'loading' && (
            <span className="pulse" style={{ width: 8, height: 8, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
          )}
          {badgeLabel}
        </span>
      </div>

      <div className="health-card__divider" />

      {/* Results */}
      {status === 'ok' && data && (
        <>
          <div className="health-card__row">
            <span className="health-card__label">Status</span>
            <span className="health-card__value">{data.status}</span>
          </div>
          <div className="health-card__row">
            <span className="health-card__label">Version</span>
            <span className="health-card__value">{data.version}</span>
          </div>
          <div className="health-card__message">{data.message}</div>
        </>
      )}

      {status === 'loading' && (
        <div className="health-card__row" style={{ justifyContent: 'center', padding: '1rem 0' }}>
          <span style={{ color: 'var(--color-text-dim)', fontSize: '0.85rem' }}>
            Waiting for backend…
          </span>
        </div>
      )}

      {status === 'error' && (
        <>
          <div className="health-card__error">{error}</div>
          <button id="retry-health-btn" className="health-card__retry-btn" onClick={checkHealth}>
            ↺ Retry
          </button>
        </>
      )}
    </div>
  );
}
