REM filepath: /Users/olgudegirmenci/Desktop/NEUAI.NA/install_requirements.bat
@echo off
:: Create a virtual environment
python -m venv venv

:: Activate the virtual environment
call venv\Scripts\activate

:: Upgrade pip
python -m pip install --upgrade pip

:: Install required packages
pip install opencv-python numpy face_recognition easyocr torch Flask

:: Install dlib separately
pip install cmake
pip install dlib


echo Installation complete.
pause