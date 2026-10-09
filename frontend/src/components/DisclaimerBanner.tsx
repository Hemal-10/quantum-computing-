import React from 'react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div
      style={{
        padding: '12px 18px',
        borderRadius: '10px',
        background: 'rgba(30, 41, 59, 0.6)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        fontSize: '0.8125rem',
        color: 'var(--color-text-secondary)',
        lineHeight: 1.5,
      }}
    >
      <div
        style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'rgba(34, 211, 238, 0.12)',
          border: '1px solid rgba(34, 211, 238, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-cyan)',
          flexShrink: 0,
          fontSize: '1rem',
        }}
      >
        ⚛
      </div>
      <div>
        <strong style={{ color: 'var(--color-text-primary)' }}>Scientific Simulation Notice:</strong>{' '}
        This platform runs classical DNA bioinformatics alongside Qiskit's local state-vector simulator (AerSimulator)
        as an educational and exploratory computational model. It does{' '}
        <strong style={{ color: '#fb7185' }}>not</strong> demonstrate physical quantum hardware speedup and is{' '}
        <strong style={{ color: '#fb7185' }}>not</strong> a clinical diagnostic tool or medical assay.
      </div>
    </div>
  );
};
