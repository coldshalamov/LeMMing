@echo off
echo Starting LeMMing...

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Starting Docker services...
docker-compose up -d --build

echo Services started. Waiting for UI to become available...
timeout /t 5 >nul

echo Opening UI in browser...
start http://localhost:3000

echo Done! You can close this window.
