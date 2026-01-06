@echo off
echo ========================================
echo Starting IPO AI Server (Auto-Restart)
echo ========================================
echo.
echo Server will be available at:
echo http://localhost:8000
echo.
echo This server will automatically restart if it crashes
echo Press Ctrl+C to stop the server permanently
echo ========================================
echo.

cd /d "%~dp0"

:restart
echo [%date% %time%] Starting server...
"C:/Users/admin/Downloads/ipo ai agent 2/.venv/Scripts/python.exe" main.py

echo.
echo [%date% %time%] Server stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak
goto restart
