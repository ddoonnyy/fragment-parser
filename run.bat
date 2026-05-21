@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python not found on PATH. Install Python 3.9+ from https://python.org and retry.
    pause
    exit /b 1
)

python -c "import requests, bs4" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -q -r requirements.txt
    if errorlevel 1 (
        echo Dependency install failed.
        pause
        exit /b 1
    )
)

python fragment_parser.py %*
echo.
pause
