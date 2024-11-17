@echo off
:: Clone the repository from GitHub
if not exist "NEUAI.NA" (
    git clone https://github.com/OlguD/NEUAI.NA.git
) else (
    cd NEUAI.NA
    git pull
    cd ..
)

cd NEUAI.NA

:: Create a virtual environment
if not exist "venv\Scripts\activate" (
    python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate

:: Upgrade pip
python -m pip install --upgrade pip

:: Install required packages
pip install -r requirements.txt

:: Install dlib separately
pip install cmake
pip install dlib


echo Installation completed.
pause