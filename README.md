# NEUAI.NA

NEUAI.NA is an application for face recognition and face similarity calculation. This project was developed by Olgu Değirmenci and Atakan Uzun as a Software Engineering graduation project.

## Features

- Face recognition and detection
- Calculating similarity between two faces
- Comparing an image from the camera with an image in the database

## Requirements

- Python 3.11+
- `opencv-python`
- `face_recognition`
- `numpy`

## Installation

1. Clone this project:
    ```bash
    git clone https://github.com/OlguD/NEUAI.NA.git
    cd NEUAI.NA
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # MacOS/Linux
    venv\Scripts\activate  # Windows
    ```

3. Install the requirements:
    ```bash
    pip install -r requirements.txt
    ```

4. Install the project:
    ```bash
    python setup.py install
    ```

## Usage

### Face Recognition and Similarity Calculation

To run the application, use the following command:
```bash
face_detection