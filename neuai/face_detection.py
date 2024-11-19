# This project was done by Olgu Değirmenci and Atakan Uzun as a graduation project in Software Engineering. 

import cv2 as cv
from threading import Thread
import time
from face_similarity import calculate_face_similarity
import logging
import sys
import numpy as np  


# Configuration
CASCADE_PATH = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/haarcascade_frontalface_default.xml"
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

def detect_face(frame):
    """Görüntüde yüz tespiti yapar"""
    try:
        # Cascade sınıflandırıcıyı yükle
        face_cascade = cv.CascadeClassifier(cv.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Gri tonlamaya çevir
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        # Yüz tespiti yap
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv.CASCADE_SCALE_IMAGE
        )
        
        # Sonuçları logla
        logging.info(f"Tespit edilen yüz sayısı: {len(faces) if isinstance(faces, np.ndarray) else 0}")
        
        return faces
        
    except Exception as e:
        logging.error(f"Yüz tespiti hatası: {str(e)}")
        return None