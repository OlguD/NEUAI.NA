from flask import Flask, render_template, Response, jsonify
import cv2 as cv
import logging
from face_new_similarity import (FaceTracker, REFERENCE_IMAGE_PATH, 
    convert_to_vector, normalize_vector, detect_face, cosine_similarity, euclidean_distance,
    interpret_similarity)
import easyocr
from document_detection import capture_image, preprocess_image, extract_info
from face_detection import detect_face, capture_video, get_frame
import numpy as np

app = Flask(__name__)

# Configuration
CASCADE_PATH = "/Users/olgudegirmenci/Desktop/NEUAI.NA/core/haarcascade_frontalface_default.xml"
# IMAGE2_PATH = '/Users/olgudegirmenci/Desktop/NEUAI.NA/core/atakan.jpeg'
VIDEO_SOURCE = 0  # or your video source

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

def generate_frames():
    capture = capture_video(VIDEO_SOURCE)
    face_tracker = FaceTracker()
    try:
        while True:
            frame = get_frame(capture)
            if frame is not None:
                faces = detect_face(frame)
                tracked_face = face_tracker.update(frame, faces)
                
                if tracked_face is not None:
                    x, y, w, h = map(int, tracked_face)
                    cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                ret, buffer = cv.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                break
    except Exception as e:
        logging.error(f"Frame üretme hatası: {e}")
    finally:
        capture.release()

def analyze_face_similarity(frame, reference_img_path):
    try:
        reference_image = cv.imread(reference_img_path)
        if reference_image is None:
            return {"error": "Referans görüntü yüklenemedi"}

        reference_vector = convert_to_vector(reference_image)
        if reference_vector is None:
            return {"error": "Referans vektör oluşturulamadı"}

        normalized_reference_vector = normalize_vector(reference_vector)
        
        faces = detect_face(frame)
        if faces is None or (isinstance(faces, np.ndarray) and len(faces) == 0):
            return {"error": "Yüz tespit edilemedi"}

        if isinstance(faces, np.ndarray) and len(faces) > 0:
            face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = map(int, face)
            face_crop = frame[y:y+h, x:x+w]
            
            detected_face_vector = convert_to_vector(face_crop)
            if detected_face_vector is None:
                return {"error": "Yüz vektörü oluşturulamadı"}

            normalized_detected_vector = normalize_vector(detected_face_vector)
            
            cos_sim = cosine_similarity(normalized_reference_vector, normalized_detected_vector)
            euc_dist = euclidean_distance(normalized_reference_vector, normalized_detected_vector)
            
            result = interpret_similarity(cos_sim, euc_dist)
            logging.info(f"Analiz sonucu: {result}")  # Sonucu logla
            return result
        else:
            return {"error": "Geçerli yüz tespit edilemedi"}

    except Exception as e:
        logging.error(f"Yüz analizi hatası: {str(e)}")
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analyze_face')
def analyze_face():
    try:
        capture = capture_video(VIDEO_SOURCE)
        frame = get_frame(capture)
        if frame is not None:
            result = analyze_face_similarity(frame, REFERENCE_IMAGE_PATH)
            logging.info(f"API sonucu: {result}")  # API sonucunu logla
            capture.release()
            return jsonify(result)
        capture.release()
        return jsonify({"error": "Frame alınamadı"})
    except Exception as e:
        logging.error(f"Analiz hatası: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/document_analysis')
def document_analysis():
    try:
        image = capture_image()
        if image is not None:
            processed = preprocess_image(image)
            reader = easyocr.Reader(['tr', 'en'])
            results = reader.readtext(processed)
            texts = [result[1] for result in results]
            boxes = [result[0] for result in results]
            info = extract_info(texts, boxes)
            return jsonify(info)
        return jsonify({"error": "No image captured"})
    except Exception as e:
        logging.error(f"Error analyzing document: {e}")
        return jsonify({"error": "An error occurred"})

if __name__ == '__main__':
    app.run(debug=True)