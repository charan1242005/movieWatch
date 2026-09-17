// Runtime-configurable API base URL. In Docker, the entrypoint script
// rewrites this value from the API_BASE_URL environment variable at
// container start, so no rebuild is needed to point at a different backend.
window.__MOVIEWATCH_API_BASE__ = "http://localhost:8000";
