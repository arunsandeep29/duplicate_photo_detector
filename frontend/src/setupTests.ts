import '@testing-library/jest-dom/extend-expect';
import userEvent from '@testing-library/user-event';
import { fireEvent as rtlFireEvent } from '@testing-library/react';

// Expose commonly-used testing utilities as globals so older tests can use them
// without importing them directly (keeps tests concise).
// Note: Adding globals is intentionally small and only for test convenience.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
;(global as any).user = userEvent;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
;(global as any).fireEvent = rtlFireEvent;

// Provide a dynamic global getter for frequently queried buttons used in tests
// This keeps older tests working without changing every test file.
Object.defineProperty(globalThis as any, 'moveButton', {
  get: () =>
    (document.querySelector('button.move-button') as HTMLButtonElement) ??
    (document.querySelector('button[aria-label*="Move"]') as HTMLButtonElement) ??
    (document.querySelector('button[aria-label*="move"]') as HTMLButtonElement),
  configurable: true,
});
