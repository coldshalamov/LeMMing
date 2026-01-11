@echo off
title LeMMing - Stop All Services
color 0C

echo.
echo ========================================
echo    Stopping LeMMing Services...
echo ========================================
echo.

REM Kill Python processes running lemming
echo Stopping Python API Server...
taskkill /FI "WINDOWTITLE eq LeMMing API Server*" /F >nul 2>&1

REM Kill Node processes running Next.js
echo Stopping Next.js Dashboard...
taskkill /FI "WINDOWTITLE eq LeMMing Dashboard*" /F >nul 2>&1

echo.
echo All LeMMing services stopped.
echo.
timeout /t 2 /nobreak >nul
