# This project was done by Olgu Değirmenci and Atakan Uzun as a graduation project in Software Engineering. 

import cv2 as cv
from threading import Thread
import time
from face_similarity import calculate_face_similarity
import logging
import sys

# Configuration
CASCADE_PATH = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/haarcascade_frontalface_default.xml"
IMAGE2_PATH = '/Users/olgudegirmenci/Desktop/NEUAI.NA/core/IMG_1546.jpg'
VIDEO_SOURCE = 0  # or your video source

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def capture_video(src):
    capture = cv.VideoCapture(src)
    if not capture.isOpened():
        logging.error(f"Error opening video source: {src}")
        sys.exit(1)
    capture.set(cv.CAP_PROP_BUFFERSIZE, 2)
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

def detect_face(camera_frame):
    gray_camera = cv.cvtColor(camera_frame, cv.COLOR_BGR2GRAY)
    face_classifier = cv.CascadeClassifier(CASCADE_PATH)
    faces = face_classifier.detectMultiScale(
        gray_camera, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    for (x, y, w, h) in faces:
        cv.rectangle(camera_frame, (x, y), (x + w, y + h), (0, 0, 255), 4)
    img_rgb = cv.cvtColor(camera_frame, cv.COLOR_BGR2RGB)
    return img_rgb

def main():
    capture = capture_video(VIDEO_SOURCE)
    while True:
        try:
            frame = get_frame(capture)
            if frame is not None:
                detect_face(frame)
                # similarity = calculate_face_similarity(frame, IMAGE2_PATH)
                # if similarity is not None:
                #     print(f"Face similarity score: {similarity}")
                #     break
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