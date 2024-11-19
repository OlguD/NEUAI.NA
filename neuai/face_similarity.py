import face_recognition
import numpy as np
import cv2 as cv

def calculate_face_similarity(camera_frame, image2_path):
    # Convert the camera frame to RGB
    camera_frame_rgb = cv.cvtColor(camera_frame, cv.COLOR_BGR2RGB)
    
    # Load the second image from the system
    image2 = face_recognition.load_image_file(image2_path)

    # Get the face encodings
    camera_frame_encodings = face_recognition.face_encodings(camera_frame_rgb)
    image2_encodings = face_recognition.face_encodings(image2)

    if len(camera_frame_encodings) == 0:
        print("No face found in the camera frame.")
        return None

    if len(image2_encodings) == 0:
        print("No face found in the second image.")
        return None

    camera_frame_encoding = camera_frame_encodings[0]
    image2_encoding = image2_encodings[0]

    # Calculate the Euclidean distance between the encodings
    distance = np.linalg.norm(camera_frame_encoding - image2_encoding)

    # Convert distance to similarity score (0 to 1)
    similarity_score = 1 / (1 + distance)
    
    return similarity_score