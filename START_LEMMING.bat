@echo off
title LeMMing Control Center
color 0A
cd /d %~dp0

if not exist logs mkdir logs

echo.
echo ========================================
echo    LeMMing Multi-Agent Orchestrator
echo ========================================
echo.
echo Starting services...
echo Logging to %~dp0logs\
echo.

REM Start Python API Backend in new window (PowerShell for Tee-Object logging)
echo [1/2] Launching Python API Server...
start "LeMMing API Server" powershell -NoExit -Command "& {Write-Host 'Starting API...'; python -u -m lemming.cli serve 2>&1 | Tee-Object -FilePath 'logs\startup_api.log'}"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

REM Start Next.js UI in new window
echo [2/2] Launching Next.js Dashboard...
cd ui
start "LeMMing Dashboard" powershell -NoExit -Command "& {Write-Host 'Starting UI...'; npm run dev 2>&1 | Tee-Object -FilePath '..\logs\startup_ui.log'}"
cd ..

REM Wait for UI to start
timeout /t 5 /nobreak >nul

REM Open browser
echo.
echo Opening dashboard in browser...
start http://localhost:3000

echo.
echo ========================================
echo  LeMMing is now running!
echo ========================================
echo.
echo  API Server:  http://localhost:8000
echo  Dashboard:   http://localhost:3000
echo  Logs:        logs\startup_api.log
echo               logs\startup_ui.log
echo.
echo  Close this window to keep services running.
echo  Close the other windows to stop services.
echo ========================================
echo.

pause
