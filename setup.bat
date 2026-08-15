@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Finding Python 3...
where py >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo ERROR: Python 3.10 or newer was not found.
    echo Install it from https://www.python.org/downloads/windows/ and try again.
    pause
    exit /b 1
  )
  set "PYTHON_CMD=python"
)

echo [2/4] Creating .venv...
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :failed
) else (
  echo Existing virtual environment found.
)

echo [3/4] Updating packaging tools...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :failed

echo [4/4] Installing application and debugging dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto :failed

echo.
echo Setup complete. Run launch.bat to open Resonance.
pause
exit /b 0

:failed
echo.
echo Setup failed. Review the error above, then run setup.bat again.
pause
exit /b 1

