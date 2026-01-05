@echo off
echo ========================================
echo Starting IPO AI Server
echo ========================================
echo.
echo Server will be available at:
echo http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
python main.py

pause
