/* Vitest test setup – extends matchers from @testing-library/jest-dom */
import '@testing-library/jest-dom/vitest';

// Polyfill ResizeObserver for recharts ResponsiveContainer in JSDOM
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
