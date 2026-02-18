@echo off
REM Phase V - Run Script for Windows
REM This script sets up the environment and starts the FastAPI server

echo ============================================
echo Phase V: Advanced Cloud Deployment
echo Starting FastAPI Server with Dapr
echo ============================================
echo.

REM Set PYTHONPATH to include src directory
set PYTHONPATH=%~dp0src

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo Please edit .env with your actual credentials
    echo.
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet

echo.
echo ============================================
echo Starting server on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo ============================================
echo.

REM Start the server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
