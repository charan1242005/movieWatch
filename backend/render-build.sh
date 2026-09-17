#!/usr/bin/env bash
set -e
rm -rf frontend backend/app 2>/dev/null || true
mkdir -p /tmp/moviewatch-src
rm -rf /tmp/moviewatch-src/*
tar -xzf moviewatch-source.tar.gz -C /tmp/moviewatch-src
cp -R /tmp/moviewatch-src/frontend ./frontend
cp -R /tmp/moviewatch-src/backend/app ./backend/app
cp /tmp/moviewatch-src/backend/requirements.txt ./backend/requirements.txt
cp /tmp/moviewatch-src/backend/Dockerfile ./backend/Dockerfile
pip install -r backend/requirements.txt
