# NEUAI.NA

In the project of designing and developing a controlled access system for university students to exams with biometric security and face recognition systems, Python, Opencv, Machine Learning models will be used to compare students' photos, student numbers and information in the exam entry documents stored in the database before entering the exam, and if the information matches, students will be able to enter the exam, and if it does not match, it will be a software that will allow the exam proctor to exclude students from the exam. The purpose of this software will be to ensure that the common exams held in our school are carried out under equal conditions.


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