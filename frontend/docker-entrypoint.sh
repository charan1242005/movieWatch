#!/bin/sh
# Rewrites the runtime API base URL baked into config.js using the
# API_BASE_URL environment variable, so the same built image can point at
# any backend without a rebuild.
set -e
API_URL="${API_BASE_URL:-http://localhost:8000}"
CONFIG_FILE="/usr/share/nginx/html/config.js"
if [ -f "$CONFIG_FILE" ]; then
  echo "window.__MOVIEWATCH_API_BASE__ = \"${API_URL}\";" > "$CONFIG_FILE"
fi
