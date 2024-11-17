REM filepath: /Users/olgudegirmenci/Desktop/NEUAI.NA/run_app.bat
@echo off
:: Activate the virtual environment
call venv\Scripts\activate

:: Run the application with error handling
python app.py || (
    echo Failed to start app.py. Please check for errors.
    pause
    exit /b 1
)

:: Open the application in the default web browser
start http://127.0.0.1:5000


echo Script execution complete.
pause