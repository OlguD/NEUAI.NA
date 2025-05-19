@echo off
setlocal enabledelayedexpansion

REM Set console title
title NEUAI System Launcher

REM Color settings for better visibility
color 0B

cls
echo +==================================================+
echo ^|             NEUAI Recognition System             ^|
echo ^|        Face and Document Analysis Suite          ^|
echo +==================================================+
echo ^|         Made by Olgu Degirmenci and              ^|
echo ^|               Atakan Uzun                        ^|
echo +==================================================+
echo.

REM Change to the project directory
cd /d "%~dp0"

REM Check for debug mode flag
set "DEBUG_MODE="
if /i "%1"=="debug" set "DEBUG_MODE=--debug"
if /i "%1"=="-d" set "DEBUG_MODE=--debug"
if /i "%1"=="--debug" set "DEBUG_MODE=--debug"

if defined DEBUG_MODE (
    echo [+] Running in DEBUG MODE
    echo [+] Verbose logging will be enabled
    echo.
)

echo [+] Initializing environment...

REM Check for virtual environment in common locations
set "VENV_FOUND=0"

REM Check if venv directory exists in the project folder
if exist "venv\Scripts\activate.bat" (
    echo [+] Activating virtual environment from venv folder...
    call venv\Scripts\activate.bat
    set "VENV_FOUND=1"
    set "PYTHON_CMD=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\activate.bat" (
    echo [+] Activating virtual environment from .venv folder...
    call .venv\Scripts\activate.bat
    set "VENV_FOUND=1"
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else if exist "env\Scripts\activate.bat" (
    echo [+] Activating virtual environment from env folder...
    call env\Scripts\activate.bat
    set "VENV_FOUND=1"
    set "PYTHON_CMD=env\Scripts\python.exe"
)

REM If no virtual environment found, create one
if "!VENV_FOUND!"=="0" (
    echo [+] Creating new virtual environment...
    python -m venv venv 2>nul
    if !errorlevel! neq 0 (
        echo [!] Error: Python is not installed or not in PATH.
        echo [!] Please install Python 3.8 or newer and try again.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    echo [+] Installing required packages...
    pip install -e . 2>nul
    if !errorlevel! neq 0 (
        echo [!] Error installing packages. Please check your internet connection.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=venv\Scripts\python.exe"
)

REM Ensure Flask is installed
echo [+] Verifying dependencies...
pip install flask -q 2>nul
pip install psutil -q 2>nul
if !errorlevel! neq 0 (
    echo [!] Error installing dependencies. Please check your internet connection.
    pause
    exit /b 1
)

REM Verify environment is set up correctly
echo [+] Environment ready. Using Python interpreter:
where python | findstr /i "venv"
if !errorlevel! neq 0 (
    echo [!] Warning: May not be using virtual environment Python.
)
echo.

REM Check if neuai_launcher.py exists
if not exist "neuai_launcher.py" (
    echo [!] Error: neuai_launcher.py not found in current directory.
    echo [!] Please ensure all files are properly installed.
    pause
    exit /b 1
)

REM Run the application
echo.
echo [+] Launching NEUAI application...
echo [+] Application will open in your web browser automatically...
echo [+] To shut down the server AND close this window, press the 'Q' key.
if defined DEBUG_MODE echo [+] To view debug info if app freezes, press the 'D' key.
echo.

REM Run the launcher using the virtual environment Python explicitly
"%~dp0%PYTHON_CMD%" "neuai_launcher.py" %DEBUG_MODE%

REM If we get here, the Python script has exited
echo.
pause
exit /b
