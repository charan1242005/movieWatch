@echo off
title MovieWatch Server - 24/7 Background Ticket Tracker
cd /d "%~dp0"
echo ========================================================
echo   Starting MovieWatch Server with 24/7 Background Worker
echo ========================================================
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
