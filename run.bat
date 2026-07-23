@echo off
setlocal
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo The application could not start. Confirm that Python 3.10 or newer is installed.
    pause
)
