@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
if not exist "!SCRIPT_DIR!.venv" (
    echo Creating Python virtual environment...
    python -m venv "!SCRIPT_DIR!.venv"
)

echo Activating virtual environment and installing dependencies...
call "!SCRIPT_DIR!.venv\Scripts\activate.bat"
python -m pip install -q -r "!SCRIPT_DIR!requirements.txt"

echo.
echo Setup complete!
echo.
echo To start the app, run:
echo   python app.py
echo.
pause
