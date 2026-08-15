@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The virtual environment is missing. Running setup first...
  call setup.bat
  if errorlevel 1 exit /b 1
)

if not defined SPOTIFY_ANALYTICS_HOST set "SPOTIFY_ANALYTICS_HOST=127.0.0.1"
if not defined SPOTIFY_ANALYTICS_PORT set "SPOTIFY_ANALYTICS_PORT=5000"
if not defined SPOTIFY_ANALYTICS_OPEN_BROWSER set "SPOTIFY_ANALYTICS_OPEN_BROWSER=1"

echo Starting Resonance on http://%SPOTIFY_ANALYTICS_HOST%:%SPOTIFY_ANALYTICS_PORT%
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" run.py

