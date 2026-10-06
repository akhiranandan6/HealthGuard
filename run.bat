@echo off
echo ========================================
echo   HealthGuard Risk Assessment Dashboard
echo ========================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not on PATH.
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install dependencies
echo [1/2] Installing dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Launch the app
echo [2/2] Starting HealthGuard...
echo.
echo App will open at http://localhost:8501
echo Press Ctrl+C to stop the server.
echo.
python -m streamlit run app.py

pause
