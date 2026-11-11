@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0.."

echo ==^> Installing JS dependencies
call npm install
if errorlevel 1 goto :fail

where python >nul 2>nul
if errorlevel 1 (
  echo python not found on PATH. Install Python 3.11+ and re-run this script.
  goto :fail
)

if exist .venv (
  echo ==^> Reusing existing .venv
) else (
  echo ==^> Creating Python virtual environment at .venv
  python -m venv .venv
  if errorlevel 1 goto :fail
)

echo ==^> Installing Python dependencies from requirements-windows.txt
call .venv\Scripts\pip install --upgrade pip
if errorlevel 1 goto :fail
call .venv\Scripts\pip install -r requirements-windows.txt
if errorlevel 1 goto :fail

if not exist data mkdir data

if exist data\global.db (
  echo ==^> data\global.db already exists -- skipping global_init.py
  echo     it deletes and recreates global.db, wiping devices/scouts/schedule/settings;
  echo     delete data\global.db yourself first if you actually want that reset
) else (
  echo ==^> Bootstrapping data\global.db
  call .venv\Scripts\python server\global_init.py
  if errorlevel 1 goto :fail
)

echo ==^> Building per-game-year databases from games\*\*.json
call .venv\Scripts\python server\data_init.py
if errorlevel 1 goto :fail

echo.
echo Setup complete.
echo Run "npm run dev:web" to start the Vite dev server + FastAPI backend together.
endlocal
exit /b 0

:fail
endlocal
exit /b 1
