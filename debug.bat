@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat before using debug mode.
  pause
  exit /b 1
)

echo Running local health checks...
".venv\Scripts\python.exe" tools\diagnostics.py
if errorlevel 1 (
  echo.
  echo Diagnostics found a blocking problem. The development server was not started.
  pause
  exit /b 1
)

set "SPOTIFY_ANALYTICS_DEBUG=1"
set "SPOTIFY_ANALYTICS_OPEN_BROWSER=1"
echo.
echo Starting in debug mode. Detailed errors are written to logs\app.log.
".venv\Scripts\python.exe" run.py

