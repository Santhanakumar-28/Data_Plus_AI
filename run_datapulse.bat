@echo off
title DataPulse AI Launcher
echo ======================================================================
echo    Starting DataPulse AI (ExaThon India 2026 - Track 04)
echo ======================================================================
echo.

echo [1/3] Checking / Starting Exasol Personal Database...
wsl -u root podman start exasol-db-b11b26af >nul 2>&1

echo [2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "DataPulse AI - Backend Server" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [3/3] Launching React Vite Frontend on http://localhost:5173 ...
start "DataPulse AI - Frontend UI" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo [SUCCESS] Both Backend and Frontend have been launched in separate windows!
echo - Frontend URL: http://localhost:5173
echo - Backend URL:  http://127.0.0.1:8000
echo - Swagger Docs: http://127.0.0.1:8000/docs
echo ======================================================================
echo.
pause
