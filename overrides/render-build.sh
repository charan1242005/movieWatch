#!/usr/bin/env bash
set -euo pipefail
rm -rf frontend backend/app 2>/dev/null || true
mkdir -p /tmp/moviewatch-src
rm -rf /tmp/moviewatch-src/*
tar -xzf moviewatch-source.tar.gz -C /tmp/moviewatch-src
cp -R /tmp/moviewatch-src/frontend ./frontend
cp -R /tmp/moviewatch-src/backend/app ./backend/app
cp /tmp/moviewatch-src/backend/requirements.txt ./backend/requirements.txt
cp /tmp/moviewatch-src/backend/Dockerfile ./backend/Dockerfile
if [ -f overrides/backend/app/providers/public_page_provider.py ]; then cp overrides/backend/app/providers/public_page_provider.py backend/app/providers/public_page_provider.py; fi
if [ -f overrides/backend/app/services/tracker_service.py ]; then cp overrides/backend/app/services/tracker_service.py backend/app/services/tracker_service.py; fi
if [ -f overrides/backend/app/api/movies.py ]; then cp overrides/backend/app/api/movies.py backend/app/api/movies.py; fi
if [ -f overrides/frontend/public/config.js ]; then cp overrides/frontend/public/config.js frontend/public/config.js; fi
pip install -r backend/requirements.txt
