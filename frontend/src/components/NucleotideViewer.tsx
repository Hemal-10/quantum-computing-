import React from 'react';

interface NucleotideViewerProps {
  label: string;
  sequence: string;
  mismatchPositions?: number[]; // 1-based indices
  motifPositions?: number[];    // 1-based indices (start of motif)
  motifLength?: number;
  highlightColor?: 'mismatch' | 'motif';
}

export const NucleotideViewer: React.FC<NucleotideViewerProps> = ({
  label,
  sequence,
  mismatchPositions = [],
  motifPositions = [],
  motifLength = 0,
}) => {
  const mismatchSet = new Set(mismatchPositions);

  // Set of 1-based positions covered by motif matches
  const motifCovered = new Set<number>();
  if (motifLength > 0) {
    for (const start of motifPositions) {
      for (let i = 0; i < motifLength; i++) {
        motifCovered.add(start + i);
      }
    }
  }

  const gcCount = sequence.split('').filter((b) => b === 'G' || b === 'C').length;
  const gcPercent = sequence.length > 0 ? ((gcCount / sequence.length) * 100).toFixed(1) : '0.0';

  return (
    <div
      style={{
        background: 'rgba(9, 14, 28, 0.75)',
        border: '1px solid rgba(56, 189, 248, 0.15)',
        borderRadius: '12px',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: 'var(--color-text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {label}
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--color-cyan)',
              background: 'rgba(34, 211, 238, 0.1)',
              padding: '2px 8px',
              borderRadius: '4px',
              border: '1px solid rgba(34, 211, 238, 0.25)',
            }}
          >
            {sequence.length} bp
          </span>
        </div>

        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--color-text-muted)',
            display: 'flex',
            gap: '12px',
          }}
        >
          <span>GC: {gcPercent}%</span>
          {mismatchPositions.length > 0 && (
            <span style={{ color: '#fb7185' }}>
              Mismatches: {mismatchPositions.length}
            </span>
          )}
          {motifPositions.length > 0 && (
            <span style={{ color: 'var(--color-cyan)' }}>
              Motif Matches: {motifPositions.length}
            </span>
          )}
        </div>
      </div>

      {sequence.length === 0 ? (
        <div
          style={{
            padding: '20px',
            textAlign: 'center',
            color: 'var(--color-text-dim)',
            fontStyle: 'italic',
            fontSize: '0.875rem',
          }}
        >
          No sequence data provided
        </div>
      ) : (
        <div
          style={{
            display: 'flex',
            gap: '6px',
            overflowX: 'auto',
            paddingBottom: '8px',
            paddingTop: '4px',
          }}
        >
          {sequence.split('').map((base, idx) => {
            const pos = idx + 1; // 1-based index
            const isMismatch = mismatchSet.has(pos);
            const isMotif = motifCovered.has(pos);

            let chipClass = `nt-chip nt-${base.toUpperCase()}`;
            if (isMismatch) chipClass += ' nt-mismatch';
            if (isMotif) chipClass += ' nt-motif-match';

            return (
              <div key={pos} className={chipClass} title={`Pos ${pos}: ${base}`}>
                <span>{base}</span>
                <span className="pos">{pos}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
