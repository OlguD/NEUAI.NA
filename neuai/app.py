from flask import Flask, render_template, Response, jsonify
import cv2 as cv
import numpy as np
import logging
from datetime import datetime
from neuai.face_new_similarity import (FaceTracker, convert_to_vector, 
    normalize_vector, detect_face, cosine_similarity,
    euclidean_distance, interpret_similarity)
import easyocr
from neuai.document_detection import preprocess_image, extract_info
from neuai.detect_object import detect_object_type
from neuai.CameraManager import CameraManagerSingleton
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def analyze_face_similarity(frame, reference_img_path):
    """Yüz benzerliği analizi yapar"""
    try:
        reference_image = cv.imread(reference_img_path)
        if reference_image is None:
            return {"error": "Referans görüntü yüklenemedi"}

        reference_vector = convert_to_vector(reference_image)
        if reference_vector is None:
            return {"error": "Referans vektör oluşturulamadı"}

        normalized_reference_vector = normalize_vector(reference_vector)
        
        faces = detect_face(frame)
        if not isinstance(faces, np.ndarray) or faces.size == 0:
            return {"error": "Yüz tespit edilemedi"}

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
        logging.info(f"Analiz sonucu: {result}")
        return result

    except Exception as e:
        logging.error(f"Yüz analizi hatası: {str(e)}")
        return {"error": str(e)}

def analyze_document_frame(frame):
    """Belge analizi yapar"""
    try:
        processed = preprocess_image(frame)
        reader = easyocr.Reader(['tr', 'en'])
        results = reader.readtext(processed)
        
        if not results:
            return {"error": "Belgede metin tespit edilemedi"}
            
        texts = [result[1] for result in results]
        boxes = [result[0] for result in results]
        info = extract_info(texts, boxes)
        
        if not any(info.values()):
            return {"error": "Belge bilgileri okunamadı"}
            
        info['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return info
        
    except Exception as e:
        logging.error(f"Belge analiz hatası: {str(e)}")
        return {"error": str(e)}

def generate_frames():
    camera = CameraManagerSingleton()
    if not camera.start():
        return
        
    face_tracker = FaceTracker()
    
    try:
        while True:
            success, frame = camera.read_frame()
            if not success:
                continue
                
            frame = cv.flip(frame, 1)

            obj_type, confidence, obj_data = detect_object_type(frame)

            if obj_type == "face" and isinstance(obj_data, np.ndarray) and len(obj_data) > 0:
                tracked_box = face_tracker.update(frame, obj_data)
                
                if tracked_box is not None:
                    x, y, w, h = tracked_box
                    cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
            elif obj_type == "document" and obj_data is not None:
                cv.drawContours(frame, [obj_data], -1, (0, 255, 0), 2)
                face_tracker = FaceTracker()

            try:
                ret, buffer = cv.imencode('.jpg', frame, [cv.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                logging.error(f"Frame encoding error: {str(e)}")
                continue
    finally:
        camera.stop()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect_object')
def detect_object():
    camera = CameraManagerSingleton()
    if not camera.start():
        return jsonify({"error": "Could not access camera"})
        
    try:
        success, frame = camera.read_frame()
        if not success:
            return jsonify({"error": "Could not read frame"})
            
        object_type, confidence, _ = detect_object_type(frame)
        return jsonify({
            "type": object_type,
            "confidence": float(confidence)
        })
    finally:
        camera.stop()

@app.route('/analyze_face')
def analyze_face():
    camera = CameraManagerSingleton()
    if not camera.start():
        return jsonify({"error": "Could not access camera"})
        
    try:
        success, frame = camera.read_frame()
        if not success:
            return jsonify({"error": "Could not read frame"})
            
        result = analyze_face_similarity(frame, os.getenv("IMAGE2_PATH"))
        return jsonify(result)
    finally:
        camera.stop()

@app.route('/document_analysis')
def document_analysis():
    camera = CameraManagerSingleton()
    if not camera.start():
        return jsonify({"error": "Could not access camera"})
        
    try:
        success, frame = camera.read_frame()
        if not success:
            return jsonify({"error": "Could not read frame"})
            
        result = analyze_document_frame(frame)
        
        if "error" not in result:
            logging.info(f"Belge analiz sonucu: {result}")
        
        return jsonify(result)
    finally:
        camera.stop()

def main():
    """Flask sunucusunu başlatmak için bir giriş noktası."""
    app.run(debug=True)

if __name__ == '__main__':
    main()