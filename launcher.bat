@echo off
title LeMMing Launcher
cd /d "D:\GitHub\Telomere\LeMMing"
echo Starting LeMMing Web Service on port 3120...
echo.
npm --version >nul 2>&1
if errorlevel 1 (
echo ERROR: npm is not installed or not in PATH.
pause
exit /b 1
)
echo Starting Next.js Dashboard on port 3120...
cd ui
echo.
echo LeMMing is starting up...
echo This window will stay open while the service runs.
echo Access the dashboard at: http://localhost:3120
echo.
echo Press Ctrl+C to stop the service, then close this window.
echo.
echo === Starting npx next dev with increased memory ===
node --max-old-space-size=4096 node_modules/.bin/next dev --port 3120
echo.
echo Service stopped. Press any key to close this window.
pause
