@echo off
title MovieWatch Instant Ticket Sniper
cd /d "%~dp0"
echo ========================================================
echo         MovieWatch Real-Time Ticket Sniper CLI
echo ========================================================
echo.
set /p MOVIE="Enter Movie Name (e.g. Demon Slayer, Devara) or BMS Link: "
set /p CITY="Enter City (default Visakhapatnam): "
if "%CITY%"=="" set CITY=Visakhapatnam
set /p DATE="Enter Date YYYY-MM-DD (default 2026-09-25): "
if "%DATE%"=="" set DATE=2026-09-25
set /p THEATRES="Enter Theatres separated by + (default PVR CMR Central + INOX + Asian): "
if "%THEATRES%"=="" set THEATRES=PVR CMR Central + INOX + Asian
set /p INTERVAL="Check interval in seconds (default 30): "
if "%INTERVAL%"=="" set INTERVAL=30

echo.
echo Starting Sniper for %MOVIE% in %CITY% on %DATE%...
.\.venv\Scripts\python.exe sniper.py --movie "%MOVIE%" --city "%CITY%" --date "%DATE%" --theatres "%THEATRES%" --interval %INTERVAL%
pause
