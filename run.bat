@echo off
setlocal
pushd "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        py -3 app.py
    ) else (
        python app.py
    )
)
if errorlevel 1 (
    echo.
    echo Setup dependencies first: run setup.bat
    pause
)
popd
endlocal
