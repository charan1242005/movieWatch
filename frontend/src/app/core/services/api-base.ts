// Central place to configure the backend base URL.
// In production, set this via environment or a build-time replacement.
export const API_BASE = (window as any).__MOVIEWATCH_API_BASE__ || 'http://localhost:8000';
