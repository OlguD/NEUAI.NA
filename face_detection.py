# This project was done by Olgu Değirmenci and Atakan Uzun as a graduation project in Software Engineering. 

import cv2 as cv
from threading import Thread
import time
from face_similarity import calculate_face_similarity
import logging
import sys

# Configuration
CASCADE_PATH = "core/haarcascade_frontalface_default.xml"
IMAGE2_PATH = '/Users/olgudegirmenci/Desktop/NEUAI.NA/core/img1.jpeg'
VIDEO_SOURCE = 0  # or your video source

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def capture_video(src):
    logging.info(f"Attempting to open video source: {src}")
    capture = cv.VideoCapture(src)
    if not capture.isOpened():
        logging.error(f"Error opening video source: {src}")
        sys.exit(1)
    capture.set(cv.CAP_PROP_BUFFERSIZE, 2)
    logging.info("Video source opened successfully")
    return capture

def get_frame(capture):
    ret, frame = capture.read()
    if not ret:
        logging.warning("Failed to capture frame")
        return None
    return frame

def show_frame(frame):
    frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    flipped_frame = cv.flip(frame, 1)
    cv.imshow('NEUAI.NA', flipped_frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        return False
    return True

def detect_face(frame):
    face_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return faces

def main():
    capture = capture_video(VIDEO_SOURCE)
    while True:
        try:
            frame = get_frame(capture)
            if frame is not None:
                detect_face(frame)
                similarity = calculate_face_similarity(frame, IMAGE2_PATH)
                if similarity is not None:
                    print(f"Face similarity score: {similarity}")
                    break
                if not show_frame(frame):
                    break
        except AttributeError as e:
            logging.error(f"AttributeError: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            break
    capture.release()
    cv.destroyAllWindows()

# if __name__ == '__main__':
#     main()