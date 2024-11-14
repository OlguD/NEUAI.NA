# Face recognition consists of two main tasks: face identification (find
# the identity from a facial image) and face verification (verify whether
# two faces belong to the same person).

# Measuring similarity between two images is another important task in
# the field of computer vision [7, 8]. It has played an important role in
# object classification and image retrieval. In general, image similarity
# contains two types: semantic similarity and visual similarity


# This project was done by Olgu Değirmenci and Atakan Uzun as a graduation project in Software Engineering. 

import cv2 as cv
from threading import Thread
import time
from face_similarity import calculate_face_similarity

cascade_path = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/haarcascade_frontalface_default.xml"


class ThreadedCamera(object):
    def __init__(self, src=0):
        self.capture = cv.VideoCapture(src)
        self.capture.set(cv.CAP_PROP_BUFFERSIZE, 2)
       
        # FPS = 1/X
        # X = desired FPS
        self.FPS = 1/30
        self.FPS_MS = int(self.FPS * 1000)
        
        # Start frame retrieval thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
            time.sleep(self.FPS)
            
    def show_frame(self):
        flipped_frame = cv.flip(self.frame, 1)  # Flip the frame horizontally
        cv.imshow('NEUAI.NA', flipped_frame)
        cv.waitKey(self.FPS_MS)
    
    def get_frame(self):
        return self.frame


def detect_face(camera_frame):
    gray_camera = cv.cvtColor(camera_frame, cv.COLOR_BGR2GRAY)

    face_classifier = cv.CascadeClassifier(cascade_path)
    faces = face_classifier.detectMultiScale(
        gray_camera, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )

    for (x, y, w, h) in faces:
        cv.rectangle(camera_frame, (x, y), (x + w, y + h), (0, 0, 255), 4)

    img_rgb = cv.cvtColor(camera_frame, cv.COLOR_BGR2RGB)
    return img_rgb


def main():
    image2_path = '/Users/olgudegirmenci/Desktop/NEUAI.NA/core/IMG_1546.jpg'
    threaded_camera = ThreadedCamera()
    while True:
        try:
            frame = threaded_camera.get_frame()
            if frame is not None:
                detect_face(frame)
                similarity = calculate_face_similarity(frame, image2_path)
                if similarity is not None:
                    print(f"Face similarity score: {similarity}")
                    break
                threaded_camera.show_frame()
        except AttributeError:
            pass

if __name__ == '__main__':
    main()