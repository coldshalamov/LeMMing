@echo off
echo Starting LeMMing...

:: Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH.
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker daemon is not running.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Starting Docker services...
docker compose up -d --build

echo Services started. Waiting for UI to become available...
timeout /t 5 >nul

echo Opening UI in browser...
start http://localhost:3000

echo Done! You can close this window.
